"""
Sidecar Packaging for Inscenium
===============================

Package placement metadata, quality metrics, and rights information
into standardized sidecar files for distribution.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

@dataclass
class PlacementOpportunity:
    """Individual placement opportunity data"""
    opportunity_id: str
    surface_id: str
    frame_range: tuple  # (start_frame, end_frame)
    timecode_range: tuple  # (start_tc, end_tc)
    surface_coordinates: List[List[float]]  # 2D polygon points
    surface_3d_points: Optional[List[List[float]]]  # 3D coordinates
    prs_score: float
    quality_metrics: Dict[str, Any]
    placement_type: str
    recommended_content_size: tuple  # (width, height) in pixels
    brand_safety_rating: str
    rights_status: str
    metadata: Dict[str, Any]

@dataclass
class SidecarManifest:
    """Complete sidecar manifest"""
    manifest_id: str
    title_id: str
    content_hash: str
    created_at: datetime
    inscenium_version: str
    opportunities: List[PlacementOpportunity]
    video_metadata: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    rights_information: Dict[str, Any]
    quality_summary: Dict[str, Any]

class SidecarPackager:
    """Package placement opportunities into distribution-ready sidecar files"""
    
    def __init__(self, output_format: str = "json"):
        self.output_format = output_format.lower()
        self.supported_formats = ["json", "xml", "csv"]
        
        if self.output_format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {output_format}. Supported: {self.supported_formats}")
    
    def create_sidecar_manifest(self,
                               title_id: str,
                               opportunities: List[Dict[str, Any]],
                               video_metadata: Optional[Dict] = None,
                               rights_data: Optional[Dict] = None) -> SidecarManifest:
        """Create complete sidecar manifest from opportunity data"""
        try:
            manifest_id = str(uuid.uuid4())
            
            # Convert opportunity dictionaries to PlacementOpportunity objects
            placement_opportunities = []
            for opp_data in opportunities:
                opportunity = self._create_placement_opportunity(opp_data)
                if opportunity:
                    placement_opportunities.append(opportunity)
            
            # Generate content hash for integrity verification
            content_hash = self._generate_content_hash(title_id, opportunities)
            
            # Create quality summary
            quality_summary = self._create_quality_summary(placement_opportunities)
            
            # Create processing metadata
            processing_metadata = {
                "pipeline_version": "2.1.0",
                "processed_at": datetime.now().isoformat(),
                "processing_time_seconds": 125.7,  # Mock
                "total_opportunities": len(placement_opportunities),
                "quality_filtered": len([o for o in placement_opportunities if o.prs_score >= 50]),
                "algorithms_used": [
                    "depth_midas_v2",
                    "flow_raft",
                    "sgi_v1",
                    "qc_metrics_v3"
                ]
            }
            
            manifest = SidecarManifest(
                manifest_id=manifest_id,
                title_id=title_id,
                content_hash=content_hash,
                created_at=datetime.now(),
                inscenium_version="2.0.0",
                opportunities=placement_opportunities,
                video_metadata=video_metadata or {},
                processing_metadata=processing_metadata,
                rights_information=rights_data or {},
                quality_summary=quality_summary
            )
            
            logger.info(f"Created sidecar manifest {manifest_id} with {len(placement_opportunities)} opportunities")
            return manifest
            
        except Exception as e:
            logger.error(f"Sidecar manifest creation failed: {e}")
            raise
    
    def _create_placement_opportunity(self, opp_data: Dict[str, Any]) -> Optional[PlacementOpportunity]:
        """Create PlacementOpportunity from raw data"""
        try:
            # Extract required fields with defaults
            surface_id = opp_data.get("surface_id", "unknown")
            frame_range = opp_data.get("frame_range", (0, 100))
            
            # Convert frame range to timecode (assuming 30fps)
            fps = opp_data.get("fps", 30.0)
            start_tc = self._frames_to_timecode(frame_range[0], fps)
            end_tc = self._frames_to_timecode(frame_range[1], fps)
            
            # Extract surface coordinates
            coordinates = opp_data.get("surface_coordinates", [[0, 0], [100, 0], [100, 100], [0, 100]])
            
            opportunity = PlacementOpportunity(
                opportunity_id=str(uuid.uuid4()),
                surface_id=surface_id,
                frame_range=frame_range,
                timecode_range=(start_tc, end_tc),
                surface_coordinates=coordinates,
                surface_3d_points=opp_data.get("surface_3d_points"),
                prs_score=opp_data.get("prs_score", 0.0),
                quality_metrics=opp_data.get("quality_metrics", {}),
                placement_type=opp_data.get("placement_type", "billboard"),
                recommended_content_size=opp_data.get("recommended_content_size", (512, 512)),
                brand_safety_rating=opp_data.get("brand_safety_rating", "safe"),
                rights_status=opp_data.get("rights_status", "available"),
                metadata=opp_data.get("metadata", {})
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to create placement opportunity: {e}")
            return None
    
    def _frames_to_timecode(self, frame: int, fps: float) -> str:
        """Convert frame number to SMPTE timecode"""
        total_seconds = frame / fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frames = int((total_seconds % 1) * fps)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    def _generate_content_hash(self, title_id: str, opportunities: List[Dict]) -> str:
        """Generate content hash for integrity verification"""
        import hashlib
        
        # Create hash from title and opportunity data
        content_string = json.dumps({
            "title_id": title_id,
            "opportunity_count": len(opportunities),
            "opportunity_ids": [opp.get("surface_id", "") for opp in opportunities]
        }, sort_keys=True)
        
        return hashlib.sha256(content_string.encode()).hexdigest()
    
    def _create_quality_summary(self, opportunities: List[PlacementOpportunity]) -> Dict[str, Any]:
        """Create summary of opportunity quality metrics"""
        if not opportunities:
            return {}
        
        prs_scores = [opp.prs_score for opp in opportunities]
        
        return {
            "total_opportunities": len(opportunities),
            "average_prs": sum(prs_scores) / len(prs_scores),
            "min_prs": min(prs_scores),
            "max_prs": max(prs_scores),
            "high_quality_count": len([s for s in prs_scores if s >= 80]),
            "medium_quality_count": len([s for s in prs_scores if 50 <= s < 80]),
            "low_quality_count": len([s for s in prs_scores if s < 50]),
            "placement_types": self._count_placement_types(opportunities),
            "duration_stats": self._calculate_duration_stats(opportunities)
        }
    
    def _count_placement_types(self, opportunities: List[PlacementOpportunity]) -> Dict[str, int]:
        """Count opportunities by placement type"""
        type_counts = {}
        for opp in opportunities:
            ptype = opp.placement_type
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        return type_counts
    
    def _calculate_duration_stats(self, opportunities: List[PlacementOpportunity]) -> Dict[str, float]:
        """Calculate duration statistics"""
        if not opportunities:
            return {}
        
        durations = [opp.frame_range[1] - opp.frame_range[0] for opp in opportunities]
        
        return {
            "avg_duration_frames": sum(durations) / len(durations),
            "min_duration_frames": min(durations),
            "max_duration_frames": max(durations),
            "total_duration_frames": sum(durations)
        }
    
    def package_sidecar(self, manifest: SidecarManifest, output_path: Path) -> bool:
        """Package sidecar manifest into specified format"""
        try:
            if self.output_format == "json":
                return self._package_json(manifest, output_path)
            elif self.output_format == "xml":
                return self._package_xml(manifest, output_path)
            elif self.output_format == "csv":
                return self._package_csv(manifest, output_path)
            else:
                raise ValueError(f"Unsupported output format: {self.output_format}")
                
        except Exception as e:
            logger.error(f"Sidecar packaging failed: {e}")
            return False
    
    def _package_json(self, manifest: SidecarManifest, output_path: Path) -> bool:
        """Package as JSON format"""
        try:
            # Convert dataclass to dictionary
            manifest_dict = asdict(manifest)
            
            # Convert datetime objects to ISO strings
            manifest_dict["created_at"] = manifest.created_at.isoformat()
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(manifest_dict, f, indent=2, default=str)
            
            logger.info(f"JSON sidecar packaged to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"JSON packaging failed: {e}")
            return False
    
    def _package_xml(self, manifest: SidecarManifest, output_path: Path) -> bool:
        """Package as XML format"""
        try:
            # Create root XML element
            root = ET.Element("inscenium_sidecar")
            root.set("version", "2.0")
            root.set("manifest_id", manifest.manifest_id)
            
            # Manifest info
            info = ET.SubElement(root, "manifest_info")
            ET.SubElement(info, "title_id").text = manifest.title_id
            ET.SubElement(info, "created_at").text = manifest.created_at.isoformat()
            ET.SubElement(info, "content_hash").text = manifest.content_hash
            ET.SubElement(info, "inscenium_version").text = manifest.inscenium_version
            
            # Quality summary
            quality = ET.SubElement(root, "quality_summary")
            for key, value in manifest.quality_summary.items():
                elem = ET.SubElement(quality, key)
                elem.text = str(value)
            
            # Opportunities
            opportunities = ET.SubElement(root, "opportunities")
            for opp in manifest.opportunities:
                opp_elem = ET.SubElement(opportunities, "opportunity")
                opp_elem.set("id", opp.opportunity_id)
                opp_elem.set("surface_id", opp.surface_id)
                opp_elem.set("prs_score", str(opp.prs_score))
                
                # Frame range
                frame_range = ET.SubElement(opp_elem, "frame_range")
                ET.SubElement(frame_range, "start").text = str(opp.frame_range[0])
                ET.SubElement(frame_range, "end").text = str(opp.frame_range[1])
                
                # Timecode range
                tc_range = ET.SubElement(opp_elem, "timecode_range")
                ET.SubElement(tc_range, "start").text = opp.timecode_range[0]
                ET.SubElement(tc_range, "end").text = opp.timecode_range[1]
                
                # Surface coordinates
                coords = ET.SubElement(opp_elem, "surface_coordinates")
                for i, point in enumerate(opp.surface_coordinates):
                    point_elem = ET.SubElement(coords, "point")
                    point_elem.set("index", str(i))
                    ET.SubElement(point_elem, "x").text = str(point[0])
                    ET.SubElement(point_elem, "y").text = str(point[1])
            
            # Write XML
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tree = ET.ElementTree(root)
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            logger.info(f"XML sidecar packaged to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"XML packaging failed: {e}")
            return False
    
    def _package_csv(self, manifest: SidecarManifest, output_path: Path) -> bool:
        """Package as CSV format"""
        try:
            import csv
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'opportunity_id', 'surface_id', 'start_frame', 'end_frame',
                    'start_timecode', 'end_timecode', 'prs_score', 'placement_type',
                    'brand_safety_rating', 'rights_status', 'surface_coords'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for opp in manifest.opportunities:
                    # Format surface coordinates as string
                    coords_str = ';'.join([f"{p[0]},{p[1]}" for p in opp.surface_coordinates])
                    
                    row = {
                        'opportunity_id': opp.opportunity_id,
                        'surface_id': opp.surface_id,
                        'start_frame': opp.frame_range[0],
                        'end_frame': opp.frame_range[1],
                        'start_timecode': opp.timecode_range[0],
                        'end_timecode': opp.timecode_range[1],
                        'prs_score': opp.prs_score,
                        'placement_type': opp.placement_type,
                        'brand_safety_rating': opp.brand_safety_rating,
                        'rights_status': opp.rights_status,
                        'surface_coords': coords_str
                    }
                    
                    writer.writerow(row)
            
            logger.info(f"CSV sidecar packaged to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"CSV packaging failed: {e}")
            return False
    
    def validate_sidecar(self, sidecar_path: Path) -> Dict[str, Any]:
        """Validate packaged sidecar file"""
        try:
            validation_result = {
                "valid": False,
                "format": self.output_format,
                "file_size": sidecar_path.stat().st_size if sidecar_path.exists() else 0,
                "opportunities_count": 0,
                "errors": [],
                "warnings": []
            }
            
            if not sidecar_path.exists():
                validation_result["errors"].append("Sidecar file does not exist")
                return validation_result
            
            # Format-specific validation
            if self.output_format == "json":
                validation_result.update(self._validate_json_sidecar(sidecar_path))
            elif self.output_format == "xml":
                validation_result.update(self._validate_xml_sidecar(sidecar_path))
            elif self.output_format == "csv":
                validation_result.update(self._validate_csv_sidecar(sidecar_path))
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {e}"
            }
    
    def _validate_json_sidecar(self, sidecar_path: Path) -> Dict[str, Any]:
        """Validate JSON sidecar format"""
        try:
            with open(sidecar_path, 'r') as f:
                data = json.load(f)
            
            errors = []
            warnings = []
            
            # Check required fields
            required_fields = ["manifest_id", "title_id", "opportunities"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            opportunities_count = len(data.get("opportunities", []))
            
            # Validate opportunities
            for i, opp in enumerate(data.get("opportunities", [])):
                if "prs_score" not in opp:
                    warnings.append(f"Opportunity {i}: Missing PRS score")
                elif not 0 <= opp["prs_score"] <= 100:
                    warnings.append(f"Opportunity {i}: Invalid PRS score {opp['prs_score']}")
            
            return {
                "opportunities_count": opportunities_count,
                "errors": errors,
                "warnings": warnings
            }
            
        except json.JSONDecodeError as e:
            return {
                "opportunities_count": 0,
                "errors": [f"Invalid JSON format: {e}"],
                "warnings": []
            }
    
    def _validate_xml_sidecar(self, sidecar_path: Path) -> Dict[str, Any]:
        """Validate XML sidecar format"""
        try:
            tree = ET.parse(sidecar_path)
            root = tree.getroot()
            
            errors = []
            warnings = []
            
            if root.tag != "inscenium_sidecar":
                errors.append("Invalid root element")
            
            opportunities = root.find("opportunities")
            opportunities_count = len(opportunities.findall("opportunity")) if opportunities is not None else 0
            
            return {
                "opportunities_count": opportunities_count,
                "errors": errors,
                "warnings": warnings
            }
            
        except ET.ParseError as e:
            return {
                "opportunities_count": 0,
                "errors": [f"Invalid XML format: {e}"],
                "warnings": []
            }
    
    def _validate_csv_sidecar(self, sidecar_path: Path) -> Dict[str, Any]:
        """Validate CSV sidecar format"""
        try:
            import csv
            
            with open(sidecar_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                opportunities_count = sum(1 for row in reader)
            
            return {
                "opportunities_count": opportunities_count,
                "errors": [],
                "warnings": []
            }
            
        except Exception as e:
            return {
                "opportunities_count": 0,
                "errors": [f"CSV validation error: {e}"],
                "warnings": []
            }

def package_sidecar(manifest: SidecarManifest, 
                   output_path: Path,
                   output_format: str = "json") -> bool:
    """
    Convenience function to package sidecar
    
    Args:
        manifest: Sidecar manifest to package
        output_path: Output file path
        output_format: Output format (json, xml, csv)
        
    Returns:
        True if packaging successful
    """
    packager = SidecarPackager(output_format)
    return packager.package_sidecar(manifest, output_path)

# Mock sidecar packaging for testing
def mock_sidecar_packaging(title_id: str, num_opportunities: int) -> Dict[str, Any]:
    """Generate mock sidecar packaging results for CI testing"""
    return {
        "title_id": title_id,
        "manifest_id": f"manifest_{hash(title_id) % 10000:04d}",
        "opportunities_packaged": num_opportunities,
        "formats_generated": ["json", "xml", "csv"],
        "file_sizes_bytes": {
            "json": 15420,
            "xml": 18650,
            "csv": 8340
        },
        "validation_passed": True,
        "content_hash": f"sha256_{hash(str(num_opportunities)) % 100000:05d}",
        "processing_time_ms": 245.3
    }

if __name__ == "__main__":
    # Demo usage
    packager = SidecarPackager("json")
    
    # Create mock opportunities
    opportunities = [
        {
            "surface_id": "surf_001",
            "frame_range": (100, 250),
            "surface_coordinates": [[10, 10], [200, 10], [200, 150], [10, 150]],
            "prs_score": 87.5,
            "placement_type": "billboard",
            "brand_safety_rating": "safe",
            "rights_status": "available"
        },
        {
            "surface_id": "surf_002", 
            "frame_range": (300, 450),
            "surface_coordinates": [[50, 50], [300, 50], [300, 200], [50, 200]],
            "prs_score": 92.1,
            "placement_type": "wall",
            "brand_safety_rating": "safe",
            "rights_status": "licensed"
        }
    ]
    
    # Create manifest
    manifest = packager.create_sidecar_manifest("test_title_001", opportunities)
    
    # Package sidecar
    output_path = Path("output/test_sidecar.json")
    if packager.package_sidecar(manifest, output_path):
        print(f"Sidecar packaged successfully to {output_path}")
        
        # Validate
        validation = packager.validate_sidecar(output_path)
        print(f"Validation: {'PASSED' if validation['valid'] else 'FAILED'}")
        print(f"Opportunities: {validation['opportunities_count']}")
    else:
        print("Sidecar packaging failed")