# CVE Matter-Analysis OS
# Multi-stage build with optional CUDA support

# Stage 1: Base Python image
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Stage 2: CPU-only image (default)
FROM base as cpu

COPY . .

# Install dev dependencies for testing
RUN pip install --no-cache-dir -e ".[dev]"

ENTRYPOINT ["cve-matter"]
CMD ["--help"]

# Stage 3: CUDA-enabled image (optional)
FROM nvidia/cuda:12.2.0-base-ubuntu22.04 as cuda

WORKDIR /app

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Copy requirements
COPY pyproject.toml .

# Install Python dependencies including CUDA support
RUN pip install --no-cache-dir -e ".[cuda,dev]"

COPY . .

ENTRYPOINT ["cve-matter"]
CMD ["--help"]

# Default to CPU image
FROM cpu as final
