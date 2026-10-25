# Python MCP server
FROM python:3.11-slim

WORKDIR /app

# ffmpeg converts audio to Opus .ogg for voice messages
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Pinned uv binary
COPY --from=ghcr.io/astral-sh/uv:0.11.11 /uv /bin/uv

# Install dependencies exactly as locked (cached unless the lockfile changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY whatsapp.py audio.py main.py ./

# Serves MCP over HTTP when MCP_TRANSPORT=streamable-http (see docker-compose.yml)
EXPOSE 8000
CMD ["/app/.venv/bin/python", "main.py"]
