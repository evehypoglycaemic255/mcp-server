try:
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
except ModuleNotFoundError:
    # Prometheus client is optional in local antigravity run environment
    registry = None

    class _NoOpMetric:
        def labels(self, *args, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

    tool_calls_counter = _NoOpMetric()
    tool_latency = _NoOpMetric()
