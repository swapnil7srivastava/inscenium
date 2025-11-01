"""SAM2 Segmentation Runner - Stub implementation with deterministic outputs"""

import os
import numpy as np
from typing import List, Tuple, Any
from .shot_detect import Shot

def run_sam2(video_path: str, shots: List[Shot]) -> Tuple[str, str]:
    """Run SAM2 segmentation on video shots.
    
    Returns:
        Tuple of (masks_path, logits_path) - paths to saved outputs
    """
    if os.getenv("MOCK_ML_MODELS", "false").lower() == "true":
        # Return deterministic mock paths
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        masks_path = f"data/masks/{base_name}_sam2_masks.npy"
        logits_path = f"data/logits/{base_name}_sam2_logits.npy"
        
        print(f"Mock SAM2: Generated masks for {len(shots)} shots")
        return masks_path, logits_path
    
    # TODO: Implement actual SAM2 integration
    raise NotImplementedError("Real SAM2 integration pending")