FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Defaults (override via env/compose)
ENV TOPTRANS_BASE_URL="https://zp.toptrans.cz"
ENV TOPTRANS_FORMAT="json"
ENV TOPTRANS_READ_ONLY="1"

ENV MCP_TRANSPORT="http"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"
ENV MCP_PATH="/mcp/"

CMD ["python", "server.py"]
