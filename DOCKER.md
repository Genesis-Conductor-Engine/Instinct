# Docker Build Notes

## Building the Images

The CVE Matter-Analysis OS provides two Docker images:

1. **CPU-only image** (default, smaller size)
2. **CUDA-enabled image** (for GPU acceleration)

### Build Commands

```bash
# Build CPU image
docker build --target cpu -t cve-matter-analysis:cpu .

# Build CUDA image
docker build --target cuda -t cve-matter-analysis:cuda .
```

### Running with Docker Compose

```bash
# Run CPU version
docker-compose up cve-matter-cpu

# Run CUDA version (requires nvidia-docker2)
docker-compose up cve-matter-cuda
```

### Known Issues

**SSL Certificate Verification in Sandboxed Environments**

In some sandboxed or restricted network environments (like CI runners with SSL inspection), 
Docker builds may fail with SSL certificate verification errors when accessing PyPI.

**Workarounds:**

1. Use a corporate/internal PyPI mirror:
   ```dockerfile
   RUN pip install --index-url https://internal-pypi.example.com/simple/ ...
   ```

2. Use Docker BuildKit with network mode (not recommended for production):
   ```bash
   DOCKER_BUILDKIT=1 docker build --network=host ...
   ```

3. Pre-download wheels and copy them into the image

The Dockerfile is correctly structured and will work in standard Docker environments
with normal internet access.

### Security Best Practices

- Images run as non-root user (uid 1000)
- Minimal base images (Python slim, CUDA base)
- No unnecessary tools or packages
- Clean apt cache to reduce image size
- Multi-stage builds to minimize final image size

### Image Sizes (Estimated)

- CPU image: ~500MB
- CUDA image: ~2GB (includes CUDA runtime)
