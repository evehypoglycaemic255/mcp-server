import os
import uuid
import logging
import json
import psycopg2
from core.config import settings

VECTOR_BACKEND = settings.VECTOR_BACKEND
DATABASE_URL = settings.DATABASE_URL

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logging.info(f"Loading SentenceTransformer model {settings.EMBEDDING_MODEL}...")
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as e:
            logging.error(f"Failed to load sentence-transformers: {e}")
    return _embedding_model

def embed_text(text: str) -> list:
    model = get_embedding_model()
    if not model: return []
    return model.encode(text).tolist()

class ChromaBackend:
    def __init__(self):
        import chromadb
        self.CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma")
        os.makedirs(self.CHROMA_PATH, exist_ok=True)
        try:
            self.client = chromadb.PersistentClient(path=self.CHROMA_PATH)
        except Exception as e:
            logging.error(f"Chroma init failed: {e}")
            self.client = None

    def _get_collection(self, name):
        if not self.client: return None
        safe_name = name.lower().replace("_", "-")
        if len(safe_name) < 3: safe_name = f"col-{safe_name}"
        return self.client.get_or_create_collection(name=safe_name)

    def store_memory(self, project_name: str, content: str, metadata: dict, is_codebase: bool) -> bool:
        coll_name = f"{project_name}-code" if is_codebase else project_name
        collection = self._get_collection(coll_name)
        if not collection: return False
        try:
            collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[str(uuid.uuid4())]
            )
            return True
        except Exception as e:
            logging.error(f"Chroma store error: {e}")
            return False

    def search_memory(self, project_name: str, query: str, n_results: int, is_codebase: bool) -> list:
        coll_name = f"{project_name}-code" if is_codebase else project_name
        collection = self._get_collection(coll_name)
        if not collection: return []
        try:
            results = collection.query(query_texts=[query], n_results=n_results)
            if not results['documents'] or len(results['documents'][0]) == 0:
                return []
            
            docs = results['documents'][0]
            metas = results['metadatas'][0] if results['metadatas'] else [{}] * len(docs)
            return [{"logic": d, "metadata": m} for d, m in zip(docs, metas)]
        except Exception as e:
            logging.error(f"Chroma search error: {e}")
            return []

class PgVectorBackend:
    def store_memory(self, project_name: str, content: str, metadata: dict, is_codebase: bool) -> bool:
        vector = embed_text(content)
        coll_name = f"{project_name}-code" if is_codebase else project_name
        if not vector: return False
        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM projects WHERE project_name = %s", (project_name,))
                res = cur.fetchone()
                project_id = res[0] if res else None
                
                # Tránh trùng lặp khi Watchdog quét lại file
                file_name = metadata.get("file")
                if file_name and is_codebase:
                    cur.execute("DELETE FROM ai_memory_vectors WHERE project_id = %s AND collection_name = %s AND metadata::jsonb ->> 'file' = %s", (project_id, coll_name, file_name))
                
                cur.execute("""
                    INSERT INTO ai_memory_vectors (project_id, collection_name, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (project_id, coll_name, content, vector, json.dumps(metadata or {})))
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"PgVector store error: {e}")
            return False
        finally:
            if 'conn' in locals() and conn: conn.close()

    def search_memory(self, project_name: str, query: str, n_results: int, is_codebase: bool) -> list:
        vector = embed_text(query)
        coll_name = f"{project_name}-code" if is_codebase else project_name
        if not vector: return []
        try:
            conn = psycopg2.connect(DATABASE_URL)
            with conn.cursor() as cur:
                vector_str = "[" + ",".join(map(str, vector)) + "]"
                cur.execute("""
                    SELECT content, metadata, embedding <=> %s::vector as distance
                    FROM ai_memory_vectors
                    WHERE collection_name = %s
                    ORDER BY distance ASC
                    LIMIT %s
                """, (vector_str, coll_name, n_results))
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        "logic": row[0],
                        "metadata": row[1] if row[1] else {},
                        "distance": float(row[2])
                    })
                return results
        except Exception as e:
            logging.error(f"PgVector search error: {e}")
            return []
        finally:
            if 'conn' in locals() and conn: conn.close()

# Factory
if VECTOR_BACKEND == "pgvector":
    logging.info("🚀 Tích hợp công cụ PGVECTOR Backend!")
    _backend = PgVectorBackend()
else:
    logging.info("🚀 Tích hợp công cụ CHROMA Backend!")
    _backend = ChromaBackend()

def store_memory(project_name: str, content: str, metadata: dict = None, is_codebase: bool = False) -> bool:
    return _backend.store_memory(project_name, content, metadata, is_codebase)

def search_memory(project_name: str, query: str, n_results: int = 3, is_codebase: bool = False, filter_sql: str = None) -> list:
    # Ở PgVector, filter_sql có thể được append (Sẽ nâng cấp sau nếu cần filter file-level)
    return _backend.search_memory(project_name, query, n_results, is_codebase)
