"""Python bindings for CUDA compositor."""

import os
import ctypes
import numpy as np
from typing import Tuple, Optional

# Try to load CUDA shared library
try:
    if os.path.exists("render/compositor_cuda.so"):
        _cuda_lib = ctypes.CDLL("render/compositor_cuda.so")
        CUDA_AVAILABLE = True
    else:
        CUDA_AVAILABLE = False
        print("CUDA compositor not found, using CPU fallback")
except Exception as e:
    CUDA_AVAILABLE = False
    print(f"Failed to load CUDA compositor: {e}")

def composite_frame(
    base_frame: np.ndarray,
    creative_frame: np.ndarray, 
    depth_map: np.ndarray,
    alpha_mask: np.ndarray,
    creative_depth: float = 5.0
) -> np.ndarray:
    """
    Composite creative asset onto base frame using depth testing.
    
    Args:
        base_frame: Base video frame (H, W, 4) uint8 RGBA
        creative_frame: Creative asset (H, W, 4) uint8 RGBA  
        depth_map: Scene depth map (H, W) float32 in meters
        alpha_mask: Alpha mask (H, W) uint8
        creative_depth: Depth of creative placement in meters
        
    Returns:
        Composited frame (H, W, 4) uint8 RGBA
    """
    
    if not CUDA_AVAILABLE:
        return _composite_frame_cpu(base_frame, creative_frame, depth_map, alpha_mask, creative_depth)
    
    # TODO: Implement CUDA compositing call
    height, width = base_frame.shape[:2]
    
    # For now, fallback to CPU implementation
    return _composite_frame_cpu(base_frame, creative_frame, depth_map, alpha_mask, creative_depth)

def _composite_frame_cpu(
    base_frame: np.ndarray,
    creative_frame: np.ndarray,
    depth_map: np.ndarray, 
    alpha_mask: np.ndarray,
    creative_depth: float
) -> np.ndarray:
    """CPU fallback implementation."""
    
    # Ensure inputs have correct shape and dtype
    assert base_frame.shape[:2] == creative_frame.shape[:2] == depth_map.shape == alpha_mask.shape
    
    height, width = base_frame.shape[:2]
    output_frame = base_frame.copy()
    
    # Z-test mask: composite where creative is in front
    should_composite = (creative_depth < depth_map) | (depth_map <= 0)
    
    # Apply alpha blending where compositor should apply and alpha > 0
    alpha = alpha_mask.astype(np.float32) / 255.0
    alpha_3d = np.stack([alpha] * 3, axis=2)  # Expand to RGB channels
    
    # Create composite mask
    composite_mask = should_composite & (alpha > 0)
    composite_mask_3d = np.stack([composite_mask] * 3, axis=2)
    
    # Alpha blend
    blended_rgb = (
        alpha_3d * creative_frame[:, :, :3].astype(np.float32) + 
        (1 - alpha_3d) * base_frame[:, :, :3].astype(np.float32)
    )
    
    # Apply composite mask
    output_frame[:, :, :3] = np.where(
        composite_mask_3d,
        blended_rgb.astype(np.uint8),
        base_frame[:, :, :3]
    )
    
    return output_frame