# CVE Matter-Analysis OS - Docker Image
# Multi-stage build for minimal production image

# CUDA runtime stage argument (default: CUDA 12.4 on Ubuntu 22.04)
ARG CUDA_IMAGE_TAG=12.4.1-runtime-ubuntu22.04

# Build stage - build Python wheels once
FROM python:3.11-slim-bullseye AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# CUDA runtime stage
FROM nvidia/cuda:${CUDA_IMAGE_TAG} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

# Install Python 3.11, pip, and supporting tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        software-properties-common \
        tini \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3.11 \
        python3.11-venv \
        python3.11-distutils \
        python3.11-dev \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && python3.11 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user for security
RUN useradd -m -u 1000 -s /bin/bash cveanalysis

WORKDIR /app

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

# Use tini for clean signal handling in CUDA containers
ENTRYPOINT ["tini", "--"]

# Default command (will be overridden for specific tasks)
CMD ["python", "-m", "src.main"]
