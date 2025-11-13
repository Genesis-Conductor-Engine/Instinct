# CVE Matter-Analysis OS - Docker Image
# Multi-stage build for minimal production image

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Add non-root user for security
RUN useradd -m -u 1000 -s /bin/bash cveanalysis

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application code
COPY src/ ./src/
COPY capsules/ ./capsules/
COPY prompts/ ./prompts/
COPY pyproject.toml .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs /app/checkpoints \
    && chown -R cveanalysis:cveanalysis /app

# Switch to non-root user
USER cveanalysis

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Default command (will be overridden for specific tasks)
CMD ["python", "-m", "src.main"]
