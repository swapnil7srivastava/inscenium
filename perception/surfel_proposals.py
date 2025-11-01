"""
Surfel Proposal Generation for Inscenium
========================================

Generate surface element (surfel) proposals for 3D placement opportunities
by combining depth, normal, and semantic information.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
import cv2
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Surfel:
    """3D surface element with placement properties"""
    center: np.ndarray  # 3D position (x, y, z)
    normal: np.ndarray  # Surface normal vector
    size: float         # Surface area estimate
    confidence: float   # Quality confidence (0-1)
    semantic_label: str # Surface type (wall, table, screen, etc.)
    pixel_coords: Tuple[int, int]  # 2D pixel location
    depth: float        # Depth value
    planarity: float    # How planar the surface is (0-1)
    visibility: float   # Visibility score (0-1)

class SurfelProposalGenerator:
    """Generate 3D surfel proposals for placement analysis"""
    
    def __init__(self, 
                 min_surfel_size: float = 0.1,
                 max_surfel_size: float = 10.0,
                 planarity_threshold: float = 0.7):
        self.min_surfel_size = min_surfel_size
        self.max_surfel_size = max_surfel_size
        self.planarity_threshold = planarity_threshold
        
    def generate_proposals(self, 
                          depth_map: np.ndarray,
                          normal_map: np.ndarray,
                          semantic_mask: np.ndarray,
                          camera_intrinsics: Optional[Dict] = None) -> List[Surfel]:
        """
        Generate surfel proposals from depth and semantic information
        
        Args:
            depth_map: Depth values (H, W)
            normal_map: Surface normals (H, W, 3)
            semantic_mask: Semantic segmentation (H, W)
            camera_intrinsics: Camera parameters for 3D projection
            
        Returns:
            List of surfel proposals
        """
        if depth_map is None:
            logger.error("Depth map is required for surfel generation")
            return []
            
        try:
            height, width = depth_map.shape
            proposals = []
            
            # Use default camera intrinsics if not provided
            if camera_intrinsics is None:
                camera_intrinsics = self._get_default_intrinsics(width, height)
            
            # Generate candidate points using grid sampling
            candidate_points = self._sample_candidate_points(depth_map, semantic_mask)
            
            for point in candidate_points:
                surfel = self._create_surfel_proposal(
                    point, depth_map, normal_map, semantic_mask, camera_intrinsics
                )
                
                if surfel and self._is_valid_proposal(surfel):
                    proposals.append(surfel)
            
            # Filter and rank proposals
            proposals = self._filter_proposals(proposals)
            proposals = self._rank_proposals(proposals)
            
            logger.info(f"Generated {len(proposals)} surfel proposals")
            return proposals
            
        except Exception as e:
            logger.error(f"Surfel proposal generation failed: {e}")
            return []
    
    def _get_default_intrinsics(self, width: int, height: int) -> Dict:
        """Generate default camera intrinsics"""
        return {
            'fx': width * 0.8,
            'fy': height * 0.8,
            'cx': width / 2.0,
            'cy': height / 2.0
        }
    
    def _sample_candidate_points(self, depth_map: np.ndarray, semantic_mask: np.ndarray) -> List[Tuple[int, int]]:
        """Sample candidate pixel locations for surfel generation"""
        height, width = depth_map.shape
        candidates = []
        
        # Grid sampling with some randomization
        step_size = 32  # Sample every 32 pixels
        
        for y in range(step_size//2, height, step_size):
            for x in range(step_size//2, width, step_size):
                # Add some random offset
                x_offset = np.random.randint(-step_size//4, step_size//4)
                y_offset = np.random.randint(-step_size//4, step_size//4)
                
                x_sample = np.clip(x + x_offset, 0, width - 1)
                y_sample = np.clip(y + y_offset, 0, height - 1)
                
                # Check if depth is valid
                if depth_map[y_sample, x_sample] > 0.1:
                    candidates.append((x_sample, y_sample))
        
        # Add some interest point sampling
        interest_points = self._sample_interest_points(depth_map, semantic_mask)
        candidates.extend(interest_points)
        
        return candidates
    
    def _sample_interest_points(self, depth_map: np.ndarray, semantic_mask: np.ndarray) -> List[Tuple[int, int]]:
        """Sample points at depth discontinuities and semantic boundaries"""
        points = []
        
        # Find edges in depth map
        depth_edges = cv2.Canny(
            (depth_map * 255).astype(np.uint8), 50, 150
        )
        
        # Sample points along edges
        edge_points = np.where(depth_edges > 0)
        if len(edge_points[0]) > 0:
            # Subsample edge points
            n_samples = min(200, len(edge_points[0]))
            indices = np.random.choice(len(edge_points[0]), n_samples, replace=False)
            
            for idx in indices:
                y, x = edge_points[0][idx], edge_points[1][idx]
                points.append((x, y))
        
        return points
    
    def _create_surfel_proposal(self, 
                               point: Tuple[int, int],
                               depth_map: np.ndarray,
                               normal_map: Optional[np.ndarray],
                               semantic_mask: np.ndarray,
                               camera_intrinsics: Dict) -> Optional[Surfel]:
        """Create a surfel proposal at given pixel location"""
        try:
            x, y = point
            depth = depth_map[y, x]
            
            if depth <= 0.1:
                return None
            
            # Convert to 3D coordinates
            center_3d = self._pixel_to_3d(x, y, depth, camera_intrinsics)
            
            # Get surface normal (or estimate if not provided)
            if normal_map is not None:
                normal = normal_map[y, x]
                normal = normal / (np.linalg.norm(normal) + 1e-8)
            else:
                normal = self._estimate_surface_normal(x, y, depth_map)
            
            # Analyze local region for surfel properties
            region_analysis = self._analyze_local_region(x, y, depth_map, semantic_mask)
            
            # Get semantic label
            semantic_label = self._get_semantic_label(x, y, semantic_mask)
            
            surfel = Surfel(
                center=center_3d,
                normal=normal,
                size=region_analysis['size'],
                confidence=region_analysis['confidence'],
                semantic_label=semantic_label,
                pixel_coords=(x, y),
                depth=depth,
                planarity=region_analysis['planarity'],
                visibility=region_analysis['visibility']
            )
            
            return surfel
            
        except Exception as e:
            logger.debug(f"Failed to create surfel at ({x}, {y}): {e}")
            return None
    
    def _pixel_to_3d(self, x: int, y: int, depth: float, intrinsics: Dict) -> np.ndarray:
        """Convert pixel coordinates to 3D world coordinates"""
        fx, fy = intrinsics['fx'], intrinsics['fy']
        cx, cy = intrinsics['cx'], intrinsics['cy']
        
        # Back-project to 3D
        x_3d = (x - cx) * depth / fx
        y_3d = (y - cy) * depth / fy
        z_3d = depth
        
        return np.array([x_3d, y_3d, z_3d])
    
    def _estimate_surface_normal(self, x: int, y: int, depth_map: np.ndarray) -> np.ndarray:
        """Estimate surface normal from local depth gradients"""
        height, width = depth_map.shape
        
        # Get neighboring depths
        x1 = max(0, x - 1)
        x2 = min(width - 1, x + 1)
        y1 = max(0, y - 1)
        y2 = min(height - 1, y + 1)
        
        # Compute gradients
        dx = depth_map[y, x2] - depth_map[y, x1]
        dy = depth_map[y2, x] - depth_map[y1, x]
        
        # Estimate normal (simplified)
        normal = np.array([-dx, -dy, 1.0])
        normal = normal / (np.linalg.norm(normal) + 1e-8)
        
        return normal
    
    def _analyze_local_region(self, x: int, y: int, depth_map: np.ndarray, semantic_mask: np.ndarray) -> Dict[str, float]:
        """Analyze local region around surfel location"""
        height, width = depth_map.shape
        window_size = 16
        
        # Define region bounds
        x1 = max(0, x - window_size // 2)
        x2 = min(width, x + window_size // 2)
        y1 = max(0, y - window_size // 2)
        y2 = min(height, y + window_size // 2)
        
        # Extract region
        region_depth = depth_map[y1:y2, x1:x2]
        region_mask = semantic_mask[y1:y2, x1:x2] if semantic_mask is not None else None
        
        # Calculate properties
        valid_depths = region_depth[region_depth > 0.1]
        
        if len(valid_depths) < 3:
            return {
                'size': self.min_surfel_size,
                'confidence': 0.1,
                'planarity': 0.0,
                'visibility': 0.5
            }
        
        # Size estimate (based on valid region area)
        area_pixels = len(valid_depths)
        area_m2 = area_pixels * (0.01 ** 2)  # Rough conversion to m²
        size = np.clip(area_m2, self.min_surfel_size, self.max_surfel_size)
        
        # Planarity (based on depth variance)
        depth_std = np.std(valid_depths)
        depth_mean = np.mean(valid_depths)
        planarity = max(0.0, 1.0 - (depth_std / (depth_mean * 0.1)))
        
        # Confidence (based on data quality)
        confidence = min(1.0, len(valid_depths) / (window_size ** 2))
        confidence *= planarity  # Higher confidence for planar surfaces
        
        # Visibility (mock implementation)
        visibility = 0.8 + np.random.normal(0, 0.1)
        visibility = np.clip(visibility, 0.0, 1.0)
        
        return {
            'size': size,
            'confidence': confidence,
            'planarity': planarity,
            'visibility': visibility
        }
    
    def _get_semantic_label(self, x: int, y: int, semantic_mask: Optional[np.ndarray]) -> str:
        """Get semantic label for pixel location"""
        if semantic_mask is None:
            return "unknown"
        
        # Mock semantic mapping
        semantic_map = {
            0: "background",
            1: "wall",
            2: "table",
            3: "screen",
            4: "billboard",
            5: "floor",
            6: "ceiling"
        }
        
        label_id = semantic_mask[y, x] if semantic_mask.ndim == 2 else 0
        return semantic_map.get(label_id, "unknown")
    
    def _is_valid_proposal(self, surfel: Surfel) -> bool:
        """Check if surfel proposal meets quality criteria"""
        if surfel.confidence < 0.3:
            return False
        
        if surfel.planarity < self.planarity_threshold:
            return False
            
        if surfel.size < self.min_surfel_size:
            return False
            
        # Check normal validity
        if np.linalg.norm(surfel.normal) < 0.5:
            return False
            
        return True
    
    def _filter_proposals(self, proposals: List[Surfel]) -> List[Surfel]:
        """Filter overlapping and low-quality proposals"""
        if len(proposals) == 0:
            return proposals
        
        # Sort by confidence
        proposals.sort(key=lambda s: s.confidence, reverse=True)
        
        # Non-maximum suppression based on 3D distance
        filtered = []
        min_distance = 0.5  # Minimum distance between surfels (meters)
        
        for proposal in proposals:
            too_close = False
            
            for existing in filtered:
                distance = np.linalg.norm(proposal.center - existing.center)
                if distance < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                filtered.append(proposal)
        
        return filtered
    
    def _rank_proposals(self, proposals: List[Surfel]) -> List[Surfel]:
        """Rank proposals by placement suitability"""
        def placement_score(surfel: Surfel) -> float:
            score = surfel.confidence * 0.3
            score += surfel.planarity * 0.3
            score += surfel.visibility * 0.2
            score += min(surfel.size / self.max_surfel_size, 1.0) * 0.2
            
            # Bonus for certain surface types
            type_bonus = {
                "wall": 0.2,
                "billboard": 0.3,
                "screen": 0.25,
                "table": 0.15
            }.get(surfel.semantic_label, 0.0)
            
            return score + type_bonus
        
        proposals.sort(key=placement_score, reverse=True)
        return proposals

# Mock surfel generation for testing
def mock_surfel_generation(depth_map: np.ndarray) -> Dict[str, Any]:
    """Generate mock surfel analysis for CI testing"""
    height, width = depth_map.shape if len(depth_map.shape) >= 2 else (480, 640)
    
    return {
        "surfel_count": 42,
        "avg_confidence": 0.76,
        "surface_types": {
            "wall": 15,
            "table": 8,
            "screen": 6,
            "billboard": 4,
            "unknown": 9
        },
        "placement_candidates": 28,
        "high_quality_surfels": 18,
        "coverage_area_m2": 24.6
    }

if __name__ == "__main__":
    # Demo usage
    generator = SurfelProposalGenerator()
    
    # Generate mock inputs
    depth_map = np.random.rand(480, 640) * 5.0 + 1.0  # 1-6m depth
    normal_map = np.random.randn(480, 640, 3)
    semantic_mask = np.random.randint(0, 7, (480, 640))
    
    proposals = generator.generate_proposals(depth_map, normal_map, semantic_mask)
    
    print(f"Generated {len(proposals)} surfel proposals")
    if proposals:
        print(f"Best proposal: {proposals[0].semantic_label} at depth {proposals[0].depth:.2f}m")
        print(f"Confidence: {proposals[0].confidence:.3f}, Planarity: {proposals[0].planarity:.3f}")