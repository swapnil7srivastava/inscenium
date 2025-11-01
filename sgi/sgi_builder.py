"""
Scene Graph Intelligence Builder for Inscenium
==============================================

Build comprehensive scene graphs from multi-modal scene analysis,
combining spatial, temporal, and semantic information for placement intelligence.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SceneNode:
    """Node in the scene graph representing a detected entity"""
    node_id: str
    node_type: str  # object, surface, region, camera
    bbox_2d: Optional[Tuple[int, int, int, int]]  # (x1, y1, x2, y2)
    bbox_3d: Optional[Dict[str, float]]  # 3D bounding box
    confidence: float
    attributes: Dict[str, Any]
    frame_range: Tuple[int, int]  # (start_frame, end_frame)

@dataclass 
class SceneEdge:
    """Edge in scene graph representing relationships between nodes"""
    edge_id: str
    source_node: str
    target_node: str
    relationship: str  # spatial, temporal, semantic, occlusion
    confidence: float
    attributes: Dict[str, Any]

@dataclass
class SceneGraph:
    """Complete scene graph with nodes, edges, and metadata"""
    graph_id: str
    nodes: List[SceneNode]
    edges: List[SceneEdge]
    metadata: Dict[str, Any]
    temporal_extent: Tuple[int, int]
    spatial_bounds: Dict[str, float]

class SGIBuilder:
    """Build scene graphs from perception pipeline outputs"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.node_counter = 0
        self.edge_counter = 0
        
    def _get_default_config(self) -> Dict:
        """Default configuration for SGI building"""
        return {
            "min_object_confidence": 0.5,
            "min_surface_confidence": 0.6,
            "spatial_threshold": 1.0,  # meters
            "temporal_threshold": 30,   # frames
            "max_nodes": 1000,
            "enable_temporal_tracking": True,
            "enable_spatial_relations": True
        }
    
    def build_sgi(self, 
                  perception_data: Dict[str, Any],
                  video_metadata: Optional[Dict] = None) -> SceneGraph:
        """
        Build scene graph from perception pipeline results
        
        Args:
            perception_data: Combined outputs from perception modules
            video_metadata: Video-level metadata (fps, duration, etc.)
            
        Returns:
            Complete scene graph with placement intelligence
        """
        try:
            logger.info("Building scene graph from perception data")
            
            # Initialize scene graph
            graph_id = f"sgi_{hash(str(perception_data)) % 10000:04d}"
            nodes = []
            edges = []
            
            # Extract temporal bounds
            temporal_extent = self._get_temporal_extent(perception_data, video_metadata)
            
            # Extract spatial bounds 
            spatial_bounds = self._get_spatial_bounds(perception_data)
            
            # Build nodes from different perception sources
            object_nodes = self._build_object_nodes(perception_data.get("objects", {}))
            surface_nodes = self._build_surface_nodes(perception_data.get("surfaces", {}))
            region_nodes = self._build_region_nodes(perception_data.get("regions", {}))
            camera_nodes = self._build_camera_nodes(perception_data.get("camera", {}))
            
            nodes.extend(object_nodes)
            nodes.extend(surface_nodes) 
            nodes.extend(region_nodes)
            nodes.extend(camera_nodes)
            
            # Build relationships between nodes
            spatial_edges = self._build_spatial_relationships(nodes)
            temporal_edges = self._build_temporal_relationships(nodes)
            semantic_edges = self._build_semantic_relationships(nodes)
            occlusion_edges = self._build_occlusion_relationships(nodes, perception_data)
            
            edges.extend(spatial_edges)
            edges.extend(temporal_edges)
            edges.extend(semantic_edges)
            edges.extend(occlusion_edges)
            
            # Create metadata
            metadata = {
                "created_at": "2024-01-15T12:00:00Z",
                "perception_pipeline_version": "2.1.0",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "placement_opportunities": self._count_placement_opportunities(nodes),
                "quality_score": self._calculate_graph_quality(nodes, edges)
            }
            
            scene_graph = SceneGraph(
                graph_id=graph_id,
                nodes=nodes,
                edges=edges,
                metadata=metadata,
                temporal_extent=temporal_extent,
                spatial_bounds=spatial_bounds
            )
            
            logger.info(f"Built scene graph with {len(nodes)} nodes and {len(edges)} edges")
            return scene_graph
            
        except Exception as e:
            logger.error(f"Scene graph building failed: {e}")
            return self._create_empty_graph()
    
    def _get_temporal_extent(self, perception_data: Dict, video_metadata: Optional[Dict]) -> Tuple[int, int]:
        """Extract temporal bounds from perception data"""
        if video_metadata and "total_frames" in video_metadata:
            return (0, video_metadata["total_frames"])
        
        # Estimate from perception data
        max_frame = 0
        for module_data in perception_data.values():
            if isinstance(module_data, dict) and "frame_range" in module_data:
                max_frame = max(max_frame, module_data["frame_range"][1])
        
        return (0, max(max_frame, 1))
    
    def _get_spatial_bounds(self, perception_data: Dict) -> Dict[str, float]:
        """Extract spatial bounds from depth/3D data"""
        # Default bounds for mock implementation
        return {
            "min_x": -5.0, "max_x": 5.0,
            "min_y": -3.0, "max_y": 3.0, 
            "min_z": 0.5,  "max_z": 10.0
        }
    
    def _build_object_nodes(self, object_data: Dict) -> List[SceneNode]:
        """Build nodes for detected objects"""
        nodes = []
        
        # Mock object detection results
        mock_objects = [
            {"class": "person", "bbox": (100, 150, 200, 400), "conf": 0.92, "frames": (0, 150)},
            {"class": "chair", "bbox": (300, 200, 450, 380), "conf": 0.78, "frames": (10, 200)},
            {"class": "table", "bbox": (150, 250, 500, 450), "conf": 0.85, "frames": (0, 180)}
        ]
        
        for obj in mock_objects:
            if obj["conf"] >= self.config["min_object_confidence"]:
                node = SceneNode(
                    node_id=f"obj_{self.node_counter:04d}",
                    node_type="object",
                    bbox_2d=obj["bbox"],
                    bbox_3d=None,
                    confidence=obj["conf"],
                    attributes={
                        "class_name": obj["class"],
                        "is_movable": obj["class"] in ["person", "chair"],
                        "placement_target": obj["class"] in ["table", "wall", "screen"]
                    },
                    frame_range=obj["frames"]
                )
                nodes.append(node)
                self.node_counter += 1
        
        return nodes
    
    def _build_surface_nodes(self, surface_data: Dict) -> List[SceneNode]:
        """Build nodes for detected surfaces"""
        nodes = []
        
        # Mock surface detection results
        mock_surfaces = [
            {"type": "wall", "area": 12.5, "conf": 0.89, "planar": 0.92, "frames": (0, 300)},
            {"type": "table", "area": 2.1, "conf": 0.76, "planar": 0.88, "frames": (20, 250)},
            {"type": "screen", "area": 1.8, "conf": 0.82, "planar": 0.95, "frames": (50, 180)}
        ]
        
        for surf in mock_surfaces:
            if surf["conf"] >= self.config["min_surface_confidence"]:
                node = SceneNode(
                    node_id=f"surf_{self.node_counter:04d}",
                    node_type="surface", 
                    bbox_2d=None,
                    bbox_3d=None,
                    confidence=surf["conf"],
                    attributes={
                        "surface_type": surf["type"],
                        "area_m2": surf["area"],
                        "planarity": surf["planar"],
                        "placement_suitable": surf["planar"] > 0.8,
                        "visibility_score": 0.85 + np.random.normal(0, 0.1)
                    },
                    frame_range=surf["frames"]
                )
                nodes.append(node)
                self.node_counter += 1
                
        return nodes
    
    def _build_region_nodes(self, region_data: Dict) -> List[SceneNode]:
        """Build nodes for spatial regions"""
        nodes = []
        
        # Mock spatial regions (foreground, background, etc.)
        mock_regions = [
            {"type": "foreground", "depth_range": (0.5, 3.0), "conf": 0.88},
            {"type": "background", "depth_range": (5.0, 10.0), "conf": 0.76}
        ]
        
        for region in mock_regions:
            node = SceneNode(
                node_id=f"region_{self.node_counter:04d}",
                node_type="region",
                bbox_2d=None,
                bbox_3d=None,
                confidence=region["conf"],
                attributes={
                    "region_type": region["type"],
                    "depth_range": region["depth_range"],
                    "occlusion_probability": 0.3 if region["type"] == "foreground" else 0.1
                },
                frame_range=(0, 300)
            )
            nodes.append(node)
            self.node_counter += 1
            
        return nodes
    
    def _build_camera_nodes(self, camera_data: Dict) -> List[SceneNode]:
        """Build nodes for camera motion and poses"""
        nodes = []
        
        # Mock camera motion analysis
        node = SceneNode(
            node_id=f"camera_{self.node_counter:04d}",
            node_type="camera",
            bbox_2d=None,
            bbox_3d=None, 
            confidence=0.95,
            attributes={
                "motion_type": "pan_tilt",
                "motion_magnitude": 2.3,
                "stability_score": 0.78,
                "exposure_consistent": True
            },
            frame_range=(0, 300)
        )
        nodes.append(node)
        self.node_counter += 1
        
        return nodes
    
    def _build_spatial_relationships(self, nodes: List[SceneNode]) -> List[SceneEdge]:
        """Build spatial relationship edges between nodes"""
        edges = []
        
        surface_nodes = [n for n in nodes if n.node_type == "surface"]
        object_nodes = [n for n in nodes if n.node_type == "object"]
        
        # Connect objects to nearby surfaces
        for obj_node in object_nodes:
            for surf_node in surface_nodes:
                # Mock spatial proximity calculation
                if np.random.rand() > 0.6:  # 40% chance of relationship
                    relationship = "adjacent" if np.random.rand() > 0.5 else "on_surface"
                    
                    edge = SceneEdge(
                        edge_id=f"spatial_{self.edge_counter:04d}",
                        source_node=obj_node.node_id,
                        target_node=surf_node.node_id,
                        relationship=relationship,
                        confidence=0.7 + np.random.normal(0, 0.1),
                        attributes={
                            "distance_estimate": np.random.uniform(0.1, 2.0),
                            "relative_position": np.random.choice(["left", "right", "above", "below"])
                        }
                    )
                    edges.append(edge)
                    self.edge_counter += 1
        
        return edges
    
    def _build_temporal_relationships(self, nodes: List[SceneNode]) -> List[SceneEdge]:
        """Build temporal relationship edges"""
        edges = []
        
        # Find temporally overlapping nodes
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # Check temporal overlap
                overlap = self._temporal_overlap(node1.frame_range, node2.frame_range)
                
                if overlap > self.config["temporal_threshold"]:
                    edge = SceneEdge(
                        edge_id=f"temporal_{self.edge_counter:04d}",
                        source_node=node1.node_id,
                        target_node=node2.node_id,
                        relationship="co_occurs",
                        confidence=min(node1.confidence, node2.confidence),
                        attributes={
                            "overlap_frames": overlap,
                            "temporal_stability": 0.8 + np.random.normal(0, 0.1)
                        }
                    )
                    edges.append(edge)
                    self.edge_counter += 1
        
        return edges
    
    def _build_semantic_relationships(self, nodes: List[SceneNode]) -> List[SceneEdge]:
        """Build semantic relationship edges"""
        edges = []
        
        # Define semantic relationships
        semantic_pairs = [
            ("person", "chair", "uses"),
            ("object", "table", "placed_on"),
            ("table", "wall", "against")
        ]
        
        for source_type, target_type, relation in semantic_pairs:
            source_nodes = [n for n in nodes if source_type in str(n.attributes)]
            target_nodes = [n for n in nodes if target_type in str(n.attributes)]
            
            for source in source_nodes:
                for target in target_nodes:
                    if np.random.rand() > 0.7:  # 30% chance
                        edge = SceneEdge(
                            edge_id=f"semantic_{self.edge_counter:04d}",
                            source_node=source.node_id,
                            target_node=target.node_id,
                            relationship=relation,
                            confidence=0.6 + np.random.normal(0, 0.15),
                            attributes={
                                "semantic_strength": np.random.uniform(0.5, 1.0)
                            }
                        )
                        edges.append(edge)
                        self.edge_counter += 1
        
        return edges
    
    def _build_occlusion_relationships(self, nodes: List[SceneNode], perception_data: Dict) -> List[SceneEdge]:
        """Build occlusion relationship edges"""
        edges = []
        
        # Mock occlusion analysis
        surface_nodes = [n for n in nodes if n.node_type == "surface"]
        
        for i, surf1 in enumerate(surface_nodes):
            for surf2 in surface_nodes[i+1:]:
                if np.random.rand() > 0.8:  # 20% chance of occlusion
                    occluder = surf1 if np.random.rand() > 0.5 else surf2
                    occluded = surf2 if occluder == surf1 else surf1
                    
                    edge = SceneEdge(
                        edge_id=f"occlusion_{self.edge_counter:04d}",
                        source_node=occluder.node_id,
                        target_node=occluded.node_id,
                        relationship="occludes",
                        confidence=0.7,
                        attributes={
                            "occlusion_percentage": np.random.uniform(0.1, 0.8),
                            "temporal_consistency": 0.85
                        }
                    )
                    edges.append(edge)
                    self.edge_counter += 1
        
        return edges
    
    def _temporal_overlap(self, range1: Tuple[int, int], range2: Tuple[int, int]) -> int:
        """Calculate temporal overlap between two frame ranges"""
        start = max(range1[0], range2[0])
        end = min(range1[1], range2[1])
        return max(0, end - start)
    
    def _count_placement_opportunities(self, nodes: List[SceneNode]) -> int:
        """Count potential placement opportunities in scene graph"""
        suitable_surfaces = [
            n for n in nodes 
            if n.node_type == "surface" and 
            n.attributes.get("placement_suitable", False)
        ]
        return len(suitable_surfaces)
    
    def _calculate_graph_quality(self, nodes: List[SceneNode], edges: List[SceneEdge]) -> float:
        """Calculate overall quality score for the scene graph"""
        if not nodes:
            return 0.0
        
        node_quality = np.mean([n.confidence for n in nodes])
        edge_quality = np.mean([e.confidence for e in edges]) if edges else 0.5
        
        # Consider connectivity
        connectivity = len(edges) / (len(nodes) + 1)
        connectivity_score = min(1.0, connectivity / 3.0)  # Normalize
        
        return (node_quality * 0.5 + edge_quality * 0.3 + connectivity_score * 0.2)
    
    def _create_empty_graph(self) -> SceneGraph:
        """Create empty scene graph for error cases"""
        return SceneGraph(
            graph_id="empty_graph",
            nodes=[],
            edges=[],
            metadata={"error": "Failed to build scene graph"},
            temporal_extent=(0, 0),
            spatial_bounds={}
        )
    
    def export_graph(self, scene_graph: SceneGraph, output_path: Path) -> bool:
        """Export scene graph to JSON format"""
        try:
            graph_dict = {
                "graph_id": scene_graph.graph_id,
                "nodes": [asdict(node) for node in scene_graph.nodes],
                "edges": [asdict(edge) for edge in scene_graph.edges],
                "metadata": scene_graph.metadata,
                "temporal_extent": scene_graph.temporal_extent,
                "spatial_bounds": scene_graph.spatial_bounds
            }
            
            with open(output_path, 'w') as f:
                json.dump(graph_dict, f, indent=2)
            
            logger.info(f"Scene graph exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export scene graph: {e}")
            return False

def build_sgi(perception_data: Dict[str, Any], 
              video_metadata: Optional[Dict] = None,
              config: Optional[Dict] = None) -> SceneGraph:
    """
    Convenience function to build scene graph
    
    Args:
        perception_data: Perception pipeline outputs
        video_metadata: Video metadata
        config: SGI building configuration
        
    Returns:
        Built scene graph
    """
    builder = SGIBuilder(config)
    return builder.build_sgi(perception_data, video_metadata)

# Mock SGI building for testing
def mock_sgi_building(video_path: str) -> Dict[str, Any]:
    """Generate mock SGI building results for CI testing"""
    return {
        "graph_id": "sgi_1234",
        "node_count": 15,
        "edge_count": 28,
        "surface_nodes": 6,
        "object_nodes": 7,
        "region_nodes": 2,
        "placement_opportunities": 4,
        "quality_score": 0.83,
        "temporal_extent": [0, 300],
        "processing_time_ms": 1250
    }