FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

ENV DEPOTO_BASE_URL="https://server1.depoto.cz"
ENV MCP_TRANSPORT="http"
ENV MCP_HOST="0.0.0.0"
ENV MCP_PORT="8000"
ENV MCP_PATH="/mcp/"

CMD ["python", "server.py"]
