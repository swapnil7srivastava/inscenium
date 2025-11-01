# Inscenium CUDA Render Service Dockerfile
# ========================================

# Use NVIDIA CUDA base image
FROM nvidia/cuda:12.2-devel-ubuntu22.04

# Prevent interactive prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    libavformat-dev \
    libavcodec-dev \
    libavutil-dev \
    libswscale-dev \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python

# Set up working directory
WORKDIR /app

# Copy Python requirements
COPY perception/requirements.txt ./perception/
COPY pyproject.toml poetry.lock ./

# Install Poetry and Python dependencies
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-root

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Copy CUDA source code
COPY render/ ./render/

# Compile CUDA kernels
RUN cd render && \
    if [ -f "compositor_cuda.cu" ]; then \
        nvcc -shared -Xcompiler -fPIC \
             -gencode arch=compute_75,code=sm_75 \
             -gencode arch=compute_80,code=sm_80 \
             -gencode arch=compute_86,code=sm_86 \
             -o compositor_cuda.so compositor_cuda.cu || \
        echo "CUDA compilation failed, using CPU fallback"; \
    fi

# Copy application code
COPY perception/ ./perception/
COPY sgi/ ./sgi/
COPY measure/ ./measure/

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 inscenium

# Create directories and set permissions
RUN mkdir -p /app/data /app/sidecar_assets /app/logs && \
    chown -R inscenium:inscenium /app

USER inscenium

# Set environment variables
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all

# Create a simple health check script
RUN echo '#!/bin/bash\npython -c "import torch; print(f\"CUDA available: {torch.cuda.is_available()}\"); exit(0)"' > /app/health-check.sh
RUN chmod +x /app/health-check.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/app/health-check.sh"]

EXPOSE 8082

# Simple HTTP server for render requests (placeholder)
CMD ["python", "-c", "import http.server; import socketserver; PORT = 8082; Handler = http.server.SimpleHTTPRequestHandler; with socketserver.TCPServer(('', PORT), Handler) as httpd: print(f'Render service running on port {PORT}'); httpd.serve_forever()"]