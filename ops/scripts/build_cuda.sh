#!/bin/bash
set -euo pipefail

echo "Building CUDA components for Inscenium..."

# Check if CUDA is available
if ! command -v nvcc &> /dev/null; then
    echo "⚠️  CUDA compiler (nvcc) not found. Skipping CUDA build."
    echo "GPU acceleration will not be available."
    
    # Create stub shared library for CPU-only builds
    echo "Creating CPU-only stub for compositor..."
    mkdir -p render/
    touch render/compositor_cuda_stub.so
    
    exit 0
fi

# Set CUDA architecture if not specified
if [ -z "${CUDA_ARCH:-}" ]; then
    CUDA_ARCH="75,80,86,89"  # Common modern GPU architectures
fi

# Parse command line arguments
RELEASE_MODE=false
if [ "${1:-}" = "--release" ]; then
    RELEASE_MODE=true
fi

# Set compilation flags
NVCC_FLAGS="-shared -Xcompiler -fPIC"
if [ "$RELEASE_MODE" = true ]; then
    NVCC_FLAGS="$NVCC_FLAGS -O3 -DNDEBUG"
else
    NVCC_FLAGS="$NVCC_FLAGS -O2 -g -lineinfo"
fi

# Add architecture flags
for arch in $(echo $CUDA_ARCH | tr ',' ' '); do
    NVCC_FLAGS="$NVCC_FLAGS -gencode arch=compute_$arch,code=sm_$arch"
done

echo "Compiling CUDA compositor kernel..."
echo "Architecture targets: $CUDA_ARCH"

# Compile the CUDA kernel
nvcc $NVCC_FLAGS \
    -I/usr/local/cuda/include \
    -o render/compositor_cuda.so \
    render/compositor_cuda.cu

if [ $? -eq 0 ]; then
    echo "✓ CUDA compositor compiled successfully!"
    
    # Verify the shared library
    if [ -f "render/compositor_cuda.so" ]; then
        echo "✓ Shared library created: render/compositor_cuda.so"
        file render/compositor_cuda.so
    fi
    
    # Test the Python bindings
    echo "Testing Python bindings..."
    source .venv/bin/activate 2>/dev/null || true
    if python -c "from render.compositor_bindings import composite_frame; print('✓ Python bindings working')" 2>/dev/null; then
        echo "✓ Python bindings verified"
    else
        echo "⚠️  Python bindings test failed - check compositor_bindings.py"
    fi
else
    echo "✗ CUDA compilation failed"
    exit 1
fi

echo ""
echo "CUDA build complete!"
echo "Shared library: render/compositor_cuda.so"