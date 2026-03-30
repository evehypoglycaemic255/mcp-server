from prometheus_client import CollectorRegistry, Counter, Histogram

registry = CollectorRegistry()

tool_calls_counter = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool calls",
    ["tool_name", "status"],
    registry=registry,
)

tool_latency = Histogram(
    "mcp_tool_latency_seconds",
    "Tool execution latency seconds",
    ["tool_name"],
    registry=registry,
)
