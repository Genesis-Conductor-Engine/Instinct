# CVE Matter-Analysis OS
# Multi-stage build with optional CUDA support

# Stage 1: Base Python image
FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY cve_matter/ ./cve_matter/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir click requests numpy scipy pandas scikit-learn pyyaml pydantic joblib

# Stage 2: CPU-only image (default)
FROM base AS cpu

# Copy remaining files
COPY config/ ./config/
COPY tests/ ./tests/

# Install the package in development mode
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 cveuser && chown -R cveuser:cveuser /app

USER cveuser

ENTRYPOINT ["cve-matter"]
CMD ["--help"]

# Stage 3: CUDA-enabled image (optional)
FROM nvidia/cuda:12.2.0-base-ubuntu22.04 AS cuda

WORKDIR /app

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    build-essential \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Copy project files
COPY pyproject.toml .
COPY cve_matter/ ./cve_matter/
COPY config/ ./config/

# Install Python dependencies including CUDA support
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir click requests numpy scipy pandas scikit-learn pyyaml pydantic joblib

# Install the package
RUN pip3 install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 cveuser && chown -R cveuser:cveuser /app

USER cveuser

ENTRYPOINT ["cve-matter"]
CMD ["--help"]

# Default to CPU image
FROM cpu AS final
