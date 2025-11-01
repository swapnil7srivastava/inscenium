"""
Inscenium Perception Module

Computer vision pipeline for video content analysis, including:
- Shot boundary detection
- SAM2 object segmentation
- Depth estimation with MiDaS
- Optical flow with RAFT
- Surface proposal generation
- UAOR uncertainty fusion
- Saliency scoring

All components provide deterministic stubs for CI/development when MOCK_ML_MODELS=true.
"""

from .shot_detect import Shot, detect_scenes
from .sam2_runner import run_sam2
from .depth_midas import estimate_depth
from .flow_raft import estimate_flow
from .surfel_proposals import SurfaceProposal, propose_surfaces
from .uaor_fuser import fuse_uaor
from .saliency_score import compute_saliency_score

__version__ = "1.0.0"
__all__ = [
    "Shot",
    "SurfaceProposal", 
    "detect_scenes",
    "run_sam2",
    "estimate_depth",
    "estimate_flow",
    "propose_surfaces",
    "fuse_uaor",
    "compute_saliency_score",
]