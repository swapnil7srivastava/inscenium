"""UAOR heuristic scoring functions."""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    logger.warning("opencv-python-headless not available for UAOR")
    HAS_CV2 = False


def blur_estimate(frame_bgr: np.ndarray, kernel_size: int = 5) -> float:
    """
    Estimate blur level using variance of Laplacian.
    
    Returns 0.0 (very blurry) to 1.0 (sharp).
    """
    if not HAS_CV2 or frame_bgr is None or frame_bgr.size == 0:
        return 0.5  # Default neutral score
        
    try:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=kernel_size)
        variance = laplacian.var()
        
        # Normalize roughly (empirical thresholds)
        # Values typically range from 0 (very blurry) to 2000+ (very sharp)
        normalized = min(1.0, variance / 1000.0)
        
        return float(normalized)
    except Exception as e:
        logger.warning(f"Blur estimation failed: {e}")
        return 0.5


def uncertainty_score(track_ctx: Dict[str, Any], conf_decay_alpha: float = 0.15) -> float:
    """
    Calculate uncertainty score for a track.
    
    Considers: confidence decay, blur, bbox jitter, lost count.
    Returns 0.0 (certain) to 1.0 (very uncertain).
    """
    try:
        conf = track_ctx.get("conf", 0.5)
        age = track_ctx.get("age", 1)
        lost = track_ctx.get("lost", 0)
        jitter = track_ctx.get("jitter", 0.0)
        
        # Confidence decay over time
        conf_factor = conf * np.exp(-conf_decay_alpha * age)
        
        # Lost frames penalty
        lost_factor = min(1.0, lost / 10.0)
        
        # Jitter penalty (already 0-1)
        jitter_factor = jitter
        
        # Combine factors (higher = more uncertain)
        uncertainty = 1.0 - conf_factor + lost_factor + jitter_factor
        
        return float(np.clip(uncertainty, 0.0, 1.0))
        
    except Exception as e:
        logger.warning(f"Uncertainty calculation failed: {e}")
        return 0.5


def _bbox_overlap_ratio(bbox1: List[int], bbox2: List[int]) -> float:
    """Calculate overlap ratio between two bboxes."""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    
    # Convert to [x1, y1, x2, y2]
    box1 = [x1, y1, x1 + w1, y1 + h1]
    box2 = [x2, y2, x2 + w2, y2 + h2]
    
    # Calculate intersection
    x_left = max(box1[0], box2[0])
    y_top = max(box1[1], box2[1])
    x_right = min(box1[2], box2[2])
    y_bottom = min(box1[3], box2[3])
    
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
        
    intersection = (x_right - x_left) * (y_bottom - y_top)
    area1 = w1 * h1
    
    return intersection / area1 if area1 > 0 else 0.0


def occlusion_score(frame_ctx: Dict[str, Any], tracks: List[Dict[str, Any]]) -> float:
    """
    Calculate overall occlusion score for the frame.
    
    Based on bbox overlaps and track densities.
    Returns 0.0 (no occlusion) to 1.0 (heavy occlusion).
    """
    try:
        if len(tracks) <= 1:
            return 0.0  # No occlusion possible
            
        total_overlap = 0.0
        pair_count = 0
        
        # Check all pairs of tracks
        for i in range(len(tracks)):
            for j in range(i + 1, len(tracks)):
                bbox1 = tracks[i].get("bbox", [0, 0, 1, 1])
                bbox2 = tracks[j].get("bbox", [0, 0, 1, 1])
                
                # Calculate mutual overlap
                overlap1 = _bbox_overlap_ratio(bbox1, bbox2)
                overlap2 = _bbox_overlap_ratio(bbox2, bbox1)
                max_overlap = max(overlap1, overlap2)
                
                total_overlap += max_overlap
                pair_count += 1
                
        if pair_count == 0:
            return 0.0
            
        # Average overlap ratio
        avg_overlap = total_overlap / pair_count
        
        # Add density factor (more tracks = higher potential occlusion)
        density_factor = min(1.0, len(tracks) / 10.0)
        
        occlusion = (avg_overlap + density_factor) / 2.0
        
        return float(np.clip(occlusion, 0.0, 1.0))
        
    except Exception as e:
        logger.warning(f"Occlusion calculation failed: {e}")
        return 0.0