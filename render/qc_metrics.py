"""
Quality Control Metrics for Inscenium
=====================================

Calculate Placement Readiness Score (PRS) and other quality metrics
for brand placement opportunities.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import cv2
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QualityThresholds:
    """Quality thresholds for PRS calculation"""
    min_visibility: float = 0.6
    min_planarity: float = 0.7
    min_duration: float = 2.0  # seconds
    min_area: float = 0.5      # m²
    max_motion: float = 10.0   # pixels/frame
    min_resolution: int = 64   # minimum pixels per side
    min_contrast: float = 0.3
    max_occlusion: float = 0.4

@dataclass
class PRSComponents:
    """Individual components of PRS score"""
    technical_score: float      # Technical quality (0-100)
    visibility_score: float     # Visibility analysis (0-100)
    temporal_score: float       # Temporal stability (0-100)
    spatial_score: float        # Spatial suitability (0-100)
    brand_safety_score: float   # Brand safety (0-100)
    final_prs: float           # Combined PRS (0-100)
    
class QCMetrics:
    """Quality control metrics calculator"""
    
    def __init__(self, thresholds: Optional[QualityThresholds] = None):
        self.thresholds = thresholds or QualityThresholds()
        self.fps = 30.0  # Default frame rate
        
    def calculate_prs_score(self, 
                           surface_data: Dict[str, Any],
                           temporal_data: Optional[Dict[str, Any]] = None,
                           video_metadata: Optional[Dict[str, Any]] = None) -> PRSComponents:
        """
        Calculate comprehensive Placement Readiness Score
        
        Args:
            surface_data: Surface detection and analysis results
            temporal_data: Temporal tracking and motion data
            video_metadata: Video metadata (fps, duration, etc.)
            
        Returns:
            PRS components with detailed scoring
        """
        try:
            if video_metadata and "fps" in video_metadata:
                self.fps = video_metadata["fps"]
            
            # Calculate individual score components
            technical_score = self._calculate_technical_score(surface_data)
            visibility_score = self._calculate_visibility_score(surface_data, temporal_data)
            temporal_score = self._calculate_temporal_score(surface_data, temporal_data)
            spatial_score = self._calculate_spatial_score(surface_data)
            brand_safety_score = self._calculate_brand_safety_score(surface_data)
            
            # Weighted combination for final PRS
            weights = {
                "technical": 0.25,
                "visibility": 0.25, 
                "temporal": 0.20,
                "spatial": 0.20,
                "brand_safety": 0.10
            }
            
            final_prs = (
                technical_score * weights["technical"] +
                visibility_score * weights["visibility"] +
                temporal_score * weights["temporal"] +
                spatial_score * weights["spatial"] +
                brand_safety_score * weights["brand_safety"]
            )
            
            components = PRSComponents(
                technical_score=technical_score,
                visibility_score=visibility_score,
                temporal_score=temporal_score,
                spatial_score=spatial_score,
                brand_safety_score=brand_safety_score,
                final_prs=final_prs
            )
            
            logger.info(f"Calculated PRS: {final_prs:.1f} (T:{technical_score:.1f}, V:{visibility_score:.1f}, "
                       f"Te:{temporal_score:.1f}, S:{spatial_score:.1f}, B:{brand_safety_score:.1f})")
            
            return components
            
        except Exception as e:
            logger.error(f"PRS calculation failed: {e}")
            return self._create_default_prs()
    
    def _calculate_technical_score(self, surface_data: Dict[str, Any]) -> float:
        """Calculate technical quality score (0-100)"""
        try:
            score = 0.0
            
            # Planarity score (30 points)
            planarity = surface_data.get("planarity", 0.0)
            planarity_score = min(planarity / self.thresholds.min_planarity, 1.0) * 30
            score += planarity_score
            
            # Surface area score (25 points)
            area = surface_data.get("area_m2", 0.0)
            area_score = min(area / 10.0, 1.0) * 25  # Normalize to 10m² max
            score += area_score
            
            # Resolution score (20 points)
            resolution = surface_data.get("pixel_resolution", 0)
            res_score = min(resolution / 512.0, 1.0) * 20  # Normalize to 512px
            score += res_score
            
            # Contrast score (15 points)
            contrast = surface_data.get("contrast_ratio", 0.0)
            contrast_score = min(contrast / 1.0, 1.0) * 15  # Normalize to 1.0 max
            score += contrast_score
            
            # Detection confidence (10 points)
            confidence = surface_data.get("detection_confidence", 0.0)
            confidence_score = confidence * 10
            score += confidence_score
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Technical score calculation failed: {e}")
            return 0.0
    
    def _calculate_visibility_score(self, 
                                   surface_data: Dict[str, Any], 
                                   temporal_data: Optional[Dict[str, Any]]) -> float:
        """Calculate visibility quality score (0-100)"""
        try:
            score = 0.0
            
            # Base visibility score (40 points)
            visibility = surface_data.get("visibility_score", 0.0)
            base_score = (visibility / 100.0) * 40
            score += base_score
            
            # Occlusion penalty (30 points)
            occlusion = surface_data.get("occlusion_ratio", 0.0)
            occlusion_score = max(0, 30 - (occlusion * 75))  # Heavy penalty for occlusion
            score += occlusion_score
            
            # Lighting consistency (20 points)
            lighting = surface_data.get("lighting_consistency", 0.8)  # Mock default
            lighting_score = lighting * 20
            score += lighting_score
            
            # Viewing angle quality (10 points)
            viewing_angle = surface_data.get("viewing_angle_score", 0.8)  # Mock default
            angle_score = viewing_angle * 10
            score += angle_score
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Visibility score calculation failed: {e}")
            return 0.0
    
    def _calculate_temporal_score(self, 
                                 surface_data: Dict[str, Any],
                                 temporal_data: Optional[Dict[str, Any]]) -> float:
        """Calculate temporal stability score (0-100)"""
        try:
            score = 0.0
            
            # Duration score (40 points)
            frame_count = surface_data.get("frame_count", 0)
            duration = frame_count / self.fps
            duration_score = min(duration / 10.0, 1.0) * 40  # Normalize to 10 seconds
            score += duration_score
            
            # Motion stability (30 points)
            if temporal_data:
                motion = temporal_data.get("average_motion", 0.0)
                motion_score = max(0, 30 - (motion / self.thresholds.max_motion) * 30)
                score += motion_score
            else:
                score += 20  # Default partial score
            
            # Appearance consistency (20 points)
            consistency = surface_data.get("appearance_consistency", 0.8)  # Mock
            consistency_score = consistency * 20
            score += consistency_score
            
            # Tracking quality (10 points) 
            tracking_quality = surface_data.get("tracking_quality", 0.7)  # Mock
            tracking_score = tracking_quality * 10
            score += tracking_score
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Temporal score calculation failed: {e}")
            return 0.0
    
    def _calculate_spatial_score(self, surface_data: Dict[str, Any]) -> float:
        """Calculate spatial suitability score (0-100)"""
        try:
            score = 0.0
            
            # Position in frame (25 points)
            # Center positions typically score higher
            center_x = surface_data.get("center_x", 0.5)  # Normalized 0-1
            center_y = surface_data.get("center_y", 0.5)
            
            # Calculate distance from center
            dist_from_center = np.sqrt((center_x - 0.5)**2 + (center_y - 0.5)**2)
            position_score = max(0, 25 - dist_from_center * 50)
            score += position_score
            
            # Aspect ratio suitability (20 points)
            aspect_ratio = surface_data.get("aspect_ratio", 1.0)
            # Prefer reasonable aspect ratios (0.5 to 2.0)
            if 0.5 <= aspect_ratio <= 2.0:
                aspect_score = 20
            else:
                aspect_score = max(0, 20 - abs(np.log2(aspect_ratio)) * 10)
            score += aspect_score
            
            # Depth consistency (20 points)
            depth_variance = surface_data.get("depth_variance", 0.0)
            depth_score = max(0, 20 - depth_variance * 40)
            score += depth_score
            
            # Normal orientation (20 points)
            # Surfaces facing camera score higher
            normal_dot = surface_data.get("normal_camera_dot", 0.8)  # Mock
            normal_score = abs(normal_dot) * 20
            score += normal_score
            
            # Boundary quality (15 points)
            boundary_score = surface_data.get("boundary_sharpness", 0.8) * 15
            score += boundary_score
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"Spatial score calculation failed: {e}")
            return 0.0
    
    def _calculate_brand_safety_score(self, surface_data: Dict[str, Any]) -> float:
        """Calculate brand safety score (0-100)"""
        try:
            # Mock brand safety analysis
            # In real implementation, this would analyze scene content
            
            base_safety = 85  # Default safe score
            
            # Check for problematic content (mock)
            content_flags = surface_data.get("content_flags", [])
            safety_penalties = {
                "violence": -30,
                "inappropriate": -40,
                "competitor_brand": -25,
                "unsuitable_context": -20
            }
            
            penalty = sum(safety_penalties.get(flag, 0) for flag in content_flags)
            
            # Contextual appropriateness
            context_score = surface_data.get("context_appropriateness", 0.9) * 15
            
            final_safety = base_safety + penalty + context_score
            return max(0.0, min(final_safety, 100.0))
            
        except Exception as e:
            logger.error(f"Brand safety calculation failed: {e}")
            return 50.0  # Conservative default
    
    def check_quality_thresholds(self, prs_components: PRSComponents) -> Dict[str, Any]:
        """Check if surface meets quality thresholds"""
        try:
            results = {
                "overall_pass": True,
                "prs_score": prs_components.final_prs,
                "threshold_results": {},
                "warnings": [],
                "blockers": []
            }
            
            # Check individual thresholds
            checks = [
                ("technical_quality", prs_components.technical_score, 60.0),
                ("visibility", prs_components.visibility_score, 50.0),
                ("temporal_stability", prs_components.temporal_score, 40.0),
                ("spatial_suitability", prs_components.spatial_score, 50.0),
                ("brand_safety", prs_components.brand_safety_score, 70.0)
            ]
            
            for check_name, score, threshold in checks:
                passed = score >= threshold
                results["threshold_results"][check_name] = {
                    "score": score,
                    "threshold": threshold,
                    "passed": passed
                }
                
                if not passed:
                    if score < threshold * 0.5:
                        results["blockers"].append(f"{check_name} critically low: {score:.1f}")
                        results["overall_pass"] = False
                    else:
                        results["warnings"].append(f"{check_name} below threshold: {score:.1f}")
            
            # Overall PRS threshold
            min_prs = 50.0
            if prs_components.final_prs < min_prs:
                results["overall_pass"] = False
                results["blockers"].append(f"PRS below minimum: {prs_components.final_prs:.1f} < {min_prs}")
            
            return results
            
        except Exception as e:
            logger.error(f"Quality threshold check failed: {e}")
            return {
                "overall_pass": False,
                "error": str(e),
                "prs_score": 0.0
            }
    
    def _create_default_prs(self) -> PRSComponents:
        """Create default PRS for error cases"""
        return PRSComponents(
            technical_score=0.0,
            visibility_score=0.0,
            temporal_score=0.0,
            spatial_score=0.0,
            brand_safety_score=50.0,
            final_prs=0.0
        )
    
    def analyze_surface_quality(self, 
                              image: np.ndarray,
                              mask: np.ndarray,
                              depth_map: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Analyze image-based quality metrics for surface"""
        try:
            if image is None or mask is None:
                return {}
            
            # Extract surface region
            surface_pixels = image[mask > 0]
            
            if len(surface_pixels) == 0:
                return {"error": "Empty surface region"}
            
            # Calculate basic quality metrics
            analysis = {
                "pixel_count": len(surface_pixels),
                "mean_brightness": float(np.mean(surface_pixels)),
                "brightness_std": float(np.std(surface_pixels)),
                "contrast_estimate": self._estimate_contrast(surface_pixels),
                "color_variance": self._calculate_color_variance(surface_pixels),
                "edge_sharpness": self._measure_edge_sharpness(image, mask)
            }
            
            # Add depth analysis if available
            if depth_map is not None:
                depth_analysis = self._analyze_depth_quality(depth_map, mask)
                analysis.update(depth_analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Surface quality analysis failed: {e}")
            return {"error": str(e)}
    
    def _estimate_contrast(self, pixels: np.ndarray) -> float:
        """Estimate local contrast of surface pixels"""
        if len(pixels) < 2:
            return 0.0
        
        # Use standard deviation as contrast estimate
        if pixels.ndim == 2:  # Grayscale
            contrast = np.std(pixels) / 255.0
        else:  # Color
            gray = np.mean(pixels, axis=1)
            contrast = np.std(gray) / 255.0
        
        return float(contrast)
    
    def _calculate_color_variance(self, pixels: np.ndarray) -> float:
        """Calculate color variance in surface"""
        if len(pixels) < 2:
            return 0.0
        
        if pixels.ndim == 1 or pixels.shape[1] == 1:
            return 0.0  # Grayscale
        
        # Calculate variance across color channels
        color_vars = [np.var(pixels[:, i]) for i in range(min(3, pixels.shape[1]))]
        return float(np.mean(color_vars)) / (255.0 ** 2)
    
    def _measure_edge_sharpness(self, image: np.ndarray, mask: np.ndarray) -> float:
        """Measure edge sharpness around surface boundary"""
        try:
            # Find mask edges
            edges = cv2.Canny(mask.astype(np.uint8), 50, 150)
            
            if np.sum(edges) == 0:
                return 0.0
            
            # Calculate gradient magnitude at edge pixels
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
            
            # Average gradient at edge pixels
            edge_gradients = gradient_mag[edges > 0]
            
            if len(edge_gradients) == 0:
                return 0.0
            
            return float(np.mean(edge_gradients)) / 255.0
            
        except Exception as e:
            logger.error(f"Edge sharpness measurement failed: {e}")
            return 0.0
    
    def _analyze_depth_quality(self, depth_map: np.ndarray, mask: np.ndarray) -> Dict[str, float]:
        """Analyze depth-based quality metrics"""
        try:
            surface_depths = depth_map[mask > 0]
            
            if len(surface_depths) == 0:
                return {}
            
            return {
                "depth_mean": float(np.mean(surface_depths)),
                "depth_std": float(np.std(surface_depths)),
                "depth_range": float(np.max(surface_depths) - np.min(surface_depths)),
                "depth_consistency": max(0.0, 1.0 - np.std(surface_depths) / (np.mean(surface_depths) + 1e-8))
            }
            
        except Exception as e:
            logger.error(f"Depth quality analysis failed: {e}")
            return {}

def calculate_prs_score(surface_data: Dict[str, Any],
                       temporal_data: Optional[Dict[str, Any]] = None,
                       thresholds: Optional[QualityThresholds] = None) -> PRSComponents:
    """
    Convenience function to calculate PRS score
    
    Args:
        surface_data: Surface analysis data
        temporal_data: Temporal analysis data
        thresholds: Quality thresholds
        
    Returns:
        PRS components with detailed scoring
    """
    metrics = QCMetrics(thresholds)
    return metrics.calculate_prs_score(surface_data, temporal_data)

def check_quality_thresholds(prs_components: PRSComponents) -> Dict[str, Any]:
    """
    Convenience function to check quality thresholds
    
    Args:
        prs_components: PRS score components
        
    Returns:
        Quality check results
    """
    metrics = QCMetrics()
    return metrics.check_quality_thresholds(prs_components)

# Mock quality metrics for testing
def mock_quality_metrics(surface_id: str) -> Dict[str, Any]:
    """Generate mock quality metrics for CI testing"""
    base_prs = 75 + np.random.normal(0, 10)
    
    return {
        "surface_id": surface_id,
        "prs_score": max(0, min(100, base_prs)),
        "technical_score": 78.5,
        "visibility_score": 84.2,
        "temporal_score": 71.8,
        "spatial_score": 82.1,
        "brand_safety_score": 88.5,
        "quality_grade": "A" if base_prs > 80 else "B" if base_prs > 60 else "C",
        "passes_threshold": base_prs >= 50,
        "warnings": 1 if base_prs < 70 else 0,
        "blockers": 1 if base_prs < 30 else 0
    }

if __name__ == "__main__":
    # Demo usage
    metrics = QCMetrics()
    
    # Mock surface data
    surface_data = {
        "planarity": 0.85,
        "area_m2": 2.3,
        "pixel_resolution": 256,
        "contrast_ratio": 0.7,
        "detection_confidence": 0.92,
        "visibility_score": 88.5,
        "occlusion_ratio": 0.15,
        "frame_count": 180,
        "center_x": 0.6,
        "center_y": 0.4,
        "aspect_ratio": 1.2
    }
    
    temporal_data = {
        "average_motion": 3.2,
        "tracking_quality": 0.87
    }
    
    # Calculate PRS
    prs = metrics.calculate_prs_score(surface_data, temporal_data)
    print(f"PRS Score: {prs.final_prs:.1f}")
    print(f"Components - T:{prs.technical_score:.1f}, V:{prs.visibility_score:.1f}, "
          f"Te:{prs.temporal_score:.1f}, S:{prs.spatial_score:.1f}, B:{prs.brand_safety_score:.1f}")
    
    # Check thresholds
    quality_check = metrics.check_quality_thresholds(prs)
    print(f"Quality Check - Pass: {quality_check['overall_pass']}, "
          f"Warnings: {len(quality_check['warnings'])}, Blockers: {len(quality_check['blockers'])}")