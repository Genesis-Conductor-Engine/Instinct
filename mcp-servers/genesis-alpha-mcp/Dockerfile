FROM python:3.12-slim
WORKDIR /app
COPY alpha_mcp_server /app/alpha_mcp_server
COPY alpha_mcp_init.sh /app/alpha_mcp_init.sh
ENV ALPHA_TRACE_DB=/app/data/alpha_traces.db YOLO_MODE=false
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python3 /app/alpha_mcp_server/main.py healthcheck >/dev/null
CMD ["/app/alpha_mcp_init.sh"]
