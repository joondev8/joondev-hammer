FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (src/ contents go directly into /app/)
COPY src/ .

# Run as non-root user
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Run the application
CMD ["python", "-m", "tickerloader.load_report"]
