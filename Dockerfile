FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project config first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code (src/ contents go directly into /app/)
COPY src/ .

# Run as non-root user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Default command for local use. In ECS, this is overridden by the task definition's command field.
# CMD ["python", "-m", "tickerloader.load_report"]
