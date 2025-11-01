"""
RAFT Optical Flow for Inscenium
===============================

Optical flow estimation using RAFT (Recurrent All-Pairs Field Transforms)
for tracking surface motion and temporal consistency analysis.
"""

import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any
import cv2
from pathlib import Path

logger = logging.getLogger(__name__)

class RAFTFlowEstimator:
    """RAFT-based optical flow estimation for motion analysis"""
    
    def __init__(self, model_type: str = "small", device: str = "cpu"):
        self.model_type = model_type
        self.device = device
        self.model = None
        
    def initialize(self) -> bool:
        """Initialize RAFT model"""
        try:
            # Mock initialization for development
            logger.info(f"Initializing RAFT {self.model_type} on {self.device}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize RAFT model: {e}")
            return False
    
    def estimate_flow(self, frame1: np.ndarray, frame2: np.ndarray) -> Optional[np.ndarray]:
        """
        Estimate optical flow between two consecutive frames
        
        Args:
            frame1: First frame (H, W, 3)
            frame2: Second frame (H, W, 3)
            
        Returns:
            Flow field (H, W, 2) with (dx, dy) vectors
        """
        if frame1 is None or frame2 is None:
            logger.error("Invalid input frames for flow estimation")
            return None
            
        try:
            # Mock flow estimation - use OpenCV for development
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)
            
            # Use Farneback optical flow as mock
            flow = cv2.calcOpticalFlowPyrLK(gray1, gray2, None, None)
            
            # Generate more realistic flow field
            flow_field = self._generate_mock_flow(gray1, gray2)
            
            logger.debug(f"Generated flow field: {flow_field.shape}")
            return flow_field
            
        except Exception as e:
            logger.error(f"Flow estimation failed: {e}")
            return None
    
    def _generate_mock_flow(self, frame1: np.ndarray, frame2: np.ndarray) -> np.ndarray:
        """Generate mock optical flow for development"""
        height, width = frame1.shape
        
        # Use Farneback optical flow
        flow = cv2.calcOpticalFlowPyrLK(
            frame1, frame2,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0
        )
        
        # Create flow field if points were tracked
        flow_field = np.zeros((height, width, 2), dtype=np.float32)
        
        # Add synthetic motion patterns for testing
        y_coords, x_coords = np.ogrid[:height, :width]
        
        # Simulate camera motion
        camera_dx = np.random.normal(0, 2.0)
        camera_dy = np.random.normal(0, 1.0)
        
        # Add object motion (some regions moving differently)
        object_regions = np.random.rand(height, width) > 0.7
        object_dx = np.random.normal(0, 5.0, (height, width)) * object_regions
        object_dy = np.random.normal(0, 3.0, (height, width)) * object_regions
        
        flow_field[:, :, 0] = camera_dx + object_dx
        flow_field[:, :, 1] = camera_dy + object_dy
        
        # Add some noise
        noise = np.random.normal(0, 0.5, flow_field.shape)
        flow_field += noise
        
        return flow_field
    
    def track_surface_motion(self, flow_field: np.ndarray, surface_mask: np.ndarray) -> Dict[str, Any]:
        """
        Analyze motion of a specific surface region
        
        Args:
            flow_field: Optical flow field (H, W, 2)
            surface_mask: Binary mask of surface region
            
        Returns:
            Motion analysis results
        """
        if flow_field is None or surface_mask is None:
            return {}
            
        try:
            surface_flow = flow_field[surface_mask > 0]
            
            if len(surface_flow) == 0:
                return {"error": "Empty surface region"}
            
            # Calculate motion statistics
            motion_vectors = surface_flow.reshape(-1, 2)
            motion_magnitude = np.linalg.norm(motion_vectors, axis=1)
            motion_direction = np.arctan2(motion_vectors[:, 1], motion_vectors[:, 0])
            
            analysis = {
                "mean_motion": float(np.mean(motion_magnitude)),
                "max_motion": float(np.max(motion_magnitude)),
                "motion_std": float(np.std(motion_magnitude)),
                "dominant_direction": float(np.median(motion_direction)),
                "direction_consistency": self._calculate_direction_consistency(motion_direction),
                "motion_smoothness": self._calculate_motion_smoothness(surface_flow, surface_mask),
                "surface_stability": self._calculate_stability_score(motion_magnitude)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Surface motion tracking failed: {e}")
            return {"error": str(e)}
    
    def _calculate_direction_consistency(self, directions: np.ndarray) -> float:
        """Calculate consistency of motion directions (0-1, higher = more consistent)"""
        if len(directions) < 2:
            return 0.0
        
        # Use circular statistics for angle consistency
        cos_sum = np.sum(np.cos(directions))
        sin_sum = np.sum(np.sin(directions))
        
        r = np.sqrt(cos_sum**2 + sin_sum**2) / len(directions)
        return float(r)
    
    def _calculate_motion_smoothness(self, surface_flow: np.ndarray, mask: np.ndarray) -> float:
        """Calculate spatial smoothness of motion within surface"""
        try:
            # Create a dense flow field for the surface
            height, width = mask.shape
            flow_dense = np.zeros((height, width, 2))
            flow_dense[mask > 0] = surface_flow
            
            # Calculate gradients
            grad_x = np.gradient(flow_dense, axis=1)
            grad_y = np.gradient(flow_dense, axis=0)
            
            # Smoothness is inverse of gradient magnitude
            gradient_mag = np.sqrt(grad_x[mask > 0]**2 + grad_y[mask > 0]**2)
            
            if len(gradient_mag) == 0:
                return 0.0
            
            smoothness = 1.0 / (1.0 + np.mean(gradient_mag))
            return float(smoothness)
            
        except Exception:
            return 0.5  # Default smoothness
    
    def _calculate_stability_score(self, motion_magnitudes: np.ndarray) -> float:
        """Calculate surface stability score (0-1, higher = more stable)"""
        if len(motion_magnitudes) == 0:
            return 0.0
        
        # Stable surfaces have low motion variance
        motion_var = np.var(motion_magnitudes)
        stability = 1.0 / (1.0 + motion_var)
        
        # Penalize high absolute motion
        mean_motion = np.mean(motion_magnitudes)
        motion_penalty = np.exp(-mean_motion / 5.0)
        
        return float(stability * motion_penalty)

# Mock flow estimation function for testing
def mock_flow_estimation(frame1: np.ndarray, frame2: np.ndarray) -> Dict[str, Any]:
    """Generate mock flow analysis for CI testing"""
    height, width = frame1.shape[:2] if len(frame1.shape) >= 2 else (480, 640)
    
    return {
        "flow_field_shape": (height, width, 2),
        "mean_flow_magnitude": 3.2,
        "max_flow_magnitude": 15.7,
        "dominant_motion_direction": 0.85,
        "surface_tracking": {
            "tracked_surfaces": 4,
            "stable_surfaces": 3,
            "motion_consistency": 0.78,
            "temporal_coherence": 0.82
        }
    }

if __name__ == "__main__":
    # Demo usage
    estimator = RAFTFlowEstimator()
    if estimator.initialize():
        # Generate mock frames
        frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        frame2 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        flow_field = estimator.estimate_flow(frame1, frame2)
        
        if flow_field is not None:
            print(f"Flow field generated: {flow_field.shape}")
            flow_mag = np.linalg.norm(flow_field, axis=2)
            print(f"Flow magnitude: {flow_mag.mean():.3f} ± {flow_mag.std():.3f}")
        else:
            print("Flow estimation failed")
    else:
        print("Model initialization failed")