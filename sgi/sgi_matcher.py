"""
SGI Surface Matcher for Inscenium
=================================

Match detected surfaces to brand placement opportunities using scene graph
intelligence and multi-criteria optimization.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .sgi_builder import SceneGraph, SceneNode, SceneEdge

logger = logging.getLogger(__name__)

@dataclass
class PlacementCriteria:
    """Criteria for surface placement matching"""
    min_area: float = 0.5          # Minimum surface area (m²)
    min_planarity: float = 0.7     # Minimum planarity score
    min_visibility: float = 0.6    # Minimum visibility score
    min_duration: float = 2.0      # Minimum visibility duration (seconds)
    preferred_types: List[str] = None  # Preferred surface types
    avoid_occlusion: bool = True   # Avoid occluded surfaces
    brand_safe: bool = True        # Only brand-safe environments
    
    def __post_init__(self):
        if self.preferred_types is None:
            self.preferred_types = ["wall", "billboard", "screen", "table"]

@dataclass
class SurfaceMatch:
    """A matched surface with placement scoring"""
    surface_node: SceneNode
    prs_score: float              # Placement Readiness Score
    match_confidence: float       # Matching confidence
    placement_attributes: Dict[str, Any]
    temporal_analysis: Dict[str, Any]
    spatial_context: Dict[str, Any]
    brand_safety: Dict[str, Any]

class SGIMatcher:
    """Match surfaces to placement opportunities using scene graph intelligence"""
    
    def __init__(self, criteria: Optional[PlacementCriteria] = None):
        self.criteria = criteria or PlacementCriteria()
        self.fps = 30.0  # Default frame rate
        
    def match_surfaces(self, 
                      scene_graph: SceneGraph,
                      brand_requirements: Optional[Dict] = None,
                      video_metadata: Optional[Dict] = None) -> List[SurfaceMatch]:
        """
        Match surfaces in scene graph to placement opportunities
        
        Args:
            scene_graph: Built scene graph with nodes and edges
            brand_requirements: Brand-specific placement requirements
            video_metadata: Video metadata for temporal analysis
            
        Returns:
            List of matched surfaces with PRS scores
        """
        try:
            logger.info(f"Matching surfaces in scene graph {scene_graph.graph_id}")
            
            if video_metadata and "fps" in video_metadata:
                self.fps = video_metadata["fps"]
            
            # Filter surface nodes
            surface_nodes = [
                node for node in scene_graph.nodes 
                if node.node_type == "surface"
            ]
            
            matches = []
            
            for surface_node in surface_nodes:
                # Check basic criteria
                if not self._meets_basic_criteria(surface_node):
                    continue
                
                # Analyze surface in scene context
                match = self._analyze_surface_match(
                    surface_node, scene_graph, brand_requirements
                )
                
                if match and match.prs_score >= 50.0:  # Minimum PRS threshold
                    matches.append(match)
            
            # Sort by PRS score (descending)
            matches.sort(key=lambda m: m.prs_score, reverse=True)
            
            logger.info(f"Found {len(matches)} matching surfaces")
            return matches
            
        except Exception as e:
            logger.error(f"Surface matching failed: {e}")
            return []
    
    def _meets_basic_criteria(self, surface_node: SceneNode) -> bool:
        """Check if surface meets basic placement criteria"""
        attrs = surface_node.attributes
        
        # Check surface area
        area = attrs.get("area_m2", 0.0)
        if area < self.criteria.min_area:
            return False
        
        # Check planarity
        planarity = attrs.get("planarity", 0.0)
        if planarity < self.criteria.min_planarity:
            return False
        
        # Check visibility
        visibility = attrs.get("visibility_score", 0.0)
        if visibility < self.criteria.min_visibility:
            return False
        
        # Check surface type preference
        surface_type = attrs.get("surface_type", "unknown")
        if surface_type not in self.criteria.preferred_types:
            return False
        
        # Check temporal duration
        frame_duration = surface_node.frame_range[1] - surface_node.frame_range[0]
        time_duration = frame_duration / self.fps
        if time_duration < self.criteria.min_duration:
            return False
        
        return True
    
    def _analyze_surface_match(self, 
                              surface_node: SceneNode,
                              scene_graph: SceneGraph,
                              brand_requirements: Optional[Dict]) -> Optional[SurfaceMatch]:
        """Analyze surface for placement suitability"""
        try:
            # Calculate PRS score components
            technical_score = self._calculate_technical_score(surface_node)
            temporal_score = self._calculate_temporal_score(surface_node, scene_graph)
            spatial_score = self._calculate_spatial_score(surface_node, scene_graph)
            brand_safety_score = self._calculate_brand_safety(surface_node, scene_graph, brand_requirements)
            
            # Weighted PRS calculation
            prs_score = (
                technical_score * 0.35 +
                temporal_score * 0.25 +
                spatial_score * 0.25 +
                brand_safety_score * 0.15
            )
            
            # Calculate overall match confidence
            match_confidence = min(surface_node.confidence, prs_score / 100.0)
            
            # Generate detailed analysis
            placement_attributes = self._extract_placement_attributes(surface_node)
            temporal_analysis = self._analyze_temporal_context(surface_node, scene_graph)
            spatial_context = self._analyze_spatial_context(surface_node, scene_graph)
            brand_safety = self._analyze_brand_safety(surface_node, scene_graph)
            
            match = SurfaceMatch(
                surface_node=surface_node,
                prs_score=prs_score,
                match_confidence=match_confidence,
                placement_attributes=placement_attributes,
                temporal_analysis=temporal_analysis,
                spatial_context=spatial_context,
                brand_safety=brand_safety
            )
            
            return match
            
        except Exception as e:
            logger.error(f"Surface analysis failed for {surface_node.node_id}: {e}")
            return None
    
    def _calculate_technical_score(self, surface_node: SceneNode) -> float:
        """Calculate technical quality score (0-100)"""
        attrs = surface_node.attributes
        
        # Base technical factors
        planarity_score = attrs.get("planarity", 0.0) * 30
        visibility_score = attrs.get("visibility_score", 0.0) * 30
        area_score = min(attrs.get("area_m2", 0.0) / 10.0, 1.0) * 20  # Cap at 10m²
        confidence_score = surface_node.confidence * 20
        
        technical_score = planarity_score + visibility_score + area_score + confidence_score
        
        return min(100.0, technical_score)
    
    def _calculate_temporal_score(self, surface_node: SceneNode, scene_graph: SceneGraph) -> float:
        """Calculate temporal suitability score (0-100)"""
        frame_duration = surface_node.frame_range[1] - surface_node.frame_range[0]
        time_duration = frame_duration / self.fps
        
        # Duration score (longer is better, up to 30 seconds)
        duration_score = min(time_duration / 30.0, 1.0) * 50
        
        # Temporal stability (fewer occlusion events)
        stability_score = self._calculate_temporal_stability(surface_node, scene_graph) * 30
        
        # Consistency of appearance
        consistency_score = 20  # Mock - would analyze actual appearance consistency
        
        return duration_score + stability_score + consistency_score
    
    def _calculate_spatial_score(self, surface_node: SceneNode, scene_graph: SceneGraph) -> float:
        """Calculate spatial context score (0-100)"""
        # Analyze spatial relationships
        spatial_edges = [
            edge for edge in scene_graph.edges
            if (edge.source_node == surface_node.node_id or 
                edge.target_node == surface_node.node_id) and
            "spatial" in edge.relationship
        ]
        
        # Position quality (center of frame is better)
        position_score = 40  # Mock implementation
        
        # Occlusion analysis
        occlusion_penalty = self._calculate_occlusion_penalty(surface_node, scene_graph)
        occlusion_score = max(0, 30 - occlusion_penalty)
        
        # Context richness (having related objects nearby)
        context_score = min(len(spatial_edges) * 5, 30)
        
        return position_score + occlusion_score + context_score
    
    def _calculate_brand_safety(self, 
                               surface_node: SceneNode, 
                               scene_graph: SceneGraph,
                               brand_requirements: Optional[Dict]) -> float:
        """Calculate brand safety score (0-100)"""
        if not self.criteria.brand_safe:
            return 100.0  # Skip brand safety if not required
        
        # Analyze scene content for brand safety
        safety_factors = {
            "appropriate_context": 90,  # Mock - would analyze actual content
            "no_competing_brands": 85,
            "suitable_audience": 92,
            "content_guidelines": 88
        }
        
        # Apply brand-specific requirements
        if brand_requirements:
            # Mock brand requirement processing
            if brand_requirements.get("family_friendly", True):
                safety_factors["family_friendly"] = 95
            
            if brand_requirements.get("avoid_competitors", True):
                safety_factors["competitor_check"] = 85
        
        return np.mean(list(safety_factors.values()))
    
    def _calculate_temporal_stability(self, surface_node: SceneNode, scene_graph: SceneGraph) -> float:
        """Calculate how stable the surface is temporally"""
        # Find occlusion edges involving this surface
        occlusion_edges = [
            edge for edge in scene_graph.edges
            if edge.target_node == surface_node.node_id and 
            edge.relationship == "occludes"
        ]
        
        # Calculate stability based on occlusion frequency
        if not occlusion_edges:
            return 1.0
        
        total_occlusion = sum(
            edge.attributes.get("occlusion_percentage", 0.0) 
            for edge in occlusion_edges
        )
        
        stability = max(0.0, 1.0 - total_occlusion)
        return stability
    
    def _calculate_occlusion_penalty(self, surface_node: SceneNode, scene_graph: SceneGraph) -> float:
        """Calculate penalty for surface occlusion"""
        if not self.criteria.avoid_occlusion:
            return 0.0
        
        occlusion_edges = [
            edge for edge in scene_graph.edges
            if edge.target_node == surface_node.node_id and 
            edge.relationship == "occludes"
        ]
        
        total_penalty = 0.0
        for edge in occlusion_edges:
            occlusion_pct = edge.attributes.get("occlusion_percentage", 0.0)
            total_penalty += occlusion_pct * 30  # Max 30 point penalty per occluder
        
        return min(total_penalty, 30.0)  # Cap total penalty
    
    def _extract_placement_attributes(self, surface_node: SceneNode) -> Dict[str, Any]:
        """Extract placement-relevant attributes"""
        attrs = surface_node.attributes.copy()
        
        # Add computed attributes
        frame_duration = surface_node.frame_range[1] - surface_node.frame_range[0]
        attrs["duration_seconds"] = frame_duration / self.fps
        attrs["placement_ready"] = attrs.get("placement_suitable", False)
        attrs["recommended_content_size"] = self._estimate_content_size(attrs.get("area_m2", 0.0))
        
        return attrs
    
    def _analyze_temporal_context(self, surface_node: SceneNode, scene_graph: SceneGraph) -> Dict[str, Any]:
        """Analyze temporal context of the surface"""
        frame_duration = surface_node.frame_range[1] - surface_node.frame_range[0]
        
        return {
            "start_frame": surface_node.frame_range[0],
            "end_frame": surface_node.frame_range[1],
            "duration_frames": frame_duration,
            "duration_seconds": frame_duration / self.fps,
            "temporal_stability": self._calculate_temporal_stability(surface_node, scene_graph),
            "visibility_windows": self._find_visibility_windows(surface_node, scene_graph)
        }
    
    def _analyze_spatial_context(self, surface_node: SceneNode, scene_graph: SceneGraph) -> Dict[str, Any]:
        """Analyze spatial context of the surface"""
        nearby_objects = self._find_nearby_objects(surface_node, scene_graph)
        spatial_relationships = self._get_spatial_relationships(surface_node, scene_graph)
        
        return {
            "nearby_objects": nearby_objects,
            "spatial_relationships": spatial_relationships,
            "scene_position": "center",  # Mock
            "depth_layer": "midground",   # Mock
            "viewing_angle": "frontal"    # Mock
        }
    
    def _analyze_brand_safety(self, surface_node: SceneNode, scene_graph: SceneGraph) -> Dict[str, Any]:
        """Analyze brand safety factors"""
        return {
            "content_rating": "family_friendly",
            "competitor_brands": [],
            "inappropriate_content": False,
            "context_suitability": "high",
            "audience_appropriateness": "all_ages"
        }
    
    def _estimate_content_size(self, area_m2: float) -> str:
        """Estimate recommended content size based on surface area"""
        if area_m2 < 1.0:
            return "small_logo"
        elif area_m2 < 5.0:
            return "medium_banner"
        elif area_m2 < 15.0:
            return "large_display"
        else:
            return "billboard_size"
    
    def _find_visibility_windows(self, surface_node: SceneNode, scene_graph: SceneGraph) -> List[Tuple[int, int]]:
        """Find time windows when surface is clearly visible"""
        # Mock implementation - would analyze actual occlusion data
        total_frames = surface_node.frame_range[1] - surface_node.frame_range[0]
        
        if total_frames < 30:
            return [surface_node.frame_range]
        
        # Split into visibility windows
        window_size = total_frames // 3
        windows = []
        
        for i in range(3):
            start = surface_node.frame_range[0] + i * window_size
            end = start + window_size
            if end <= surface_node.frame_range[1]:
                windows.append((start, end))
        
        return windows
    
    def _find_nearby_objects(self, surface_node: SceneNode, scene_graph: SceneGraph) -> List[str]:
        """Find objects spatially related to the surface"""
        related_edges = [
            edge for edge in scene_graph.edges
            if (edge.source_node == surface_node.node_id or 
                edge.target_node == surface_node.node_id) and
            "spatial" in edge.relationship
        ]
        
        nearby_objects = []
        for edge in related_edges:
            other_node_id = (edge.target_node if edge.source_node == surface_node.node_id 
                           else edge.source_node)
            
            # Find the node
            other_node = next((n for n in scene_graph.nodes if n.node_id == other_node_id), None)
            if other_node and other_node.node_type == "object":
                class_name = other_node.attributes.get("class_name", "unknown")
                nearby_objects.append(class_name)
        
        return nearby_objects
    
    def _get_spatial_relationships(self, surface_node: SceneNode, scene_graph: SceneGraph) -> List[Dict]:
        """Get detailed spatial relationships"""
        spatial_edges = [
            edge for edge in scene_graph.edges
            if (edge.source_node == surface_node.node_id or 
                edge.target_node == surface_node.node_id) and
            "spatial" in edge.relationship
        ]
        
        relationships = []
        for edge in spatial_edges:
            relationships.append({
                "relationship": edge.relationship,
                "confidence": edge.confidence,
                "attributes": edge.attributes
            })
        
        return relationships

def match_surfaces(scene_graph: SceneGraph,
                  criteria: Optional[PlacementCriteria] = None,
                  brand_requirements: Optional[Dict] = None,
                  video_metadata: Optional[Dict] = None) -> List[SurfaceMatch]:
    """
    Convenience function to match surfaces
    
    Args:
        scene_graph: Scene graph with surface nodes
        criteria: Placement criteria
        brand_requirements: Brand requirements
        video_metadata: Video metadata
        
    Returns:
        List of surface matches with PRS scores
    """
    matcher = SGIMatcher(criteria)
    return matcher.match_surfaces(scene_graph, brand_requirements, video_metadata)

# Mock surface matching for testing
def mock_surface_matching(scene_graph_id: str) -> Dict[str, Any]:
    """Generate mock surface matching results for CI testing"""
    return {
        "scene_graph_id": scene_graph_id,
        "total_surfaces": 6,
        "matched_surfaces": 4,
        "avg_prs_score": 84.2,
        "top_matches": [
            {"surface_id": "surf_0001", "prs_score": 92.5, "type": "wall"},
            {"surface_id": "surf_0003", "prs_score": 87.8, "type": "billboard"},
            {"surface_id": "surf_0005", "prs_score": 81.3, "type": "screen"}
        ],
        "brand_safety_score": 88.5,
        "temporal_coverage": 0.78
    }