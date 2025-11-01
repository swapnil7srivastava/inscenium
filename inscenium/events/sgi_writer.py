"""SGI event writing and zone detection."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile

logger = logging.getLogger(__name__)


def point_in_polygon(point: tuple, polygon: List[List[float]]) -> bool:
    """Test if point is inside polygon using ray casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def bbox_center(bbox: List[int]) -> tuple:
    """Get center point of bbox [x, y, w, h]."""
    x, y, w, h = bbox
    return (x + w/2, y + h/2)


class SGIWriter:
    """Write SGI events and track data to JSONL files."""
    
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.events_path = self.run_dir / "events.sgi.jsonl"
        self.tracks_path = self.run_dir / "tracks.jsonl"
        
        # Track state for zone events
        self.track_zones = {}  # track_id -> current_zone
        self.zones = []
        
    def load_zones(self, zones_path: Optional[str] = None):
        """Load zone definitions from JSON file."""
        if not zones_path:
            return
            
        try:
            with open(zones_path, 'r') as f:
                data = json.load(f)
                self.zones = data.get("zones", [])
                logger.info(f"Loaded {len(self.zones)} zones")
        except Exception as e:
            logger.warning(f"Failed to load zones from {zones_path}: {e}")
            
    def _detect_zone_events(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect zone enter/exit events for tracks."""
        events = []
        
        for track in tracks:
            track_id = track["id"]
            bbox = track["bbox"]
            center = bbox_center(bbox)
            
            # Find current zone
            current_zone = None
            for zone in self.zones:
                if point_in_polygon(center, zone["polygon"]):
                    current_zone = zone["name"]
                    break
                    
            # Check for zone changes
            previous_zone = self.track_zones.get(track_id)
            
            if previous_zone != current_zone:
                # Exit previous zone
                if previous_zone is not None:
                    events.append({
                        "type": "zone_exit",
                        "track_id": track_id,
                        "zone": previous_zone
                    })
                    
                # Enter new zone
                if current_zone is not None:
                    events.append({
                        "type": "zone_enter", 
                        "track_id": track_id,
                        "zone": current_zone
                    })
                    
                # Update state
                self.track_zones[track_id] = current_zone
                
        return events
        
    def write_frame_data(self, frame_idx: int, ts_sec: float, 
                        objects: List[Dict[str, Any]], 
                        tracks: List[Dict[str, Any]],
                        uaor_scores: Dict[str, float]):
        """Write frame data to SGI and tracks files."""
        try:
            # Detect zone events
            zone_events = self._detect_zone_events(tracks)
            
            # Write SGI event data
            sgi_data = {
                "ts": ts_sec,
                "frame": frame_idx,
                "objects": [
                    {
                        "id": obj.get("id", -1),
                        "label": obj["label"],
                        "bbox": obj["bbox"], 
                        "conf": obj["conf"]
                    }
                    for obj in objects
                ],
                "events": zone_events,
                "uaor": {
                    "occlusion": uaor_scores.get("occlusion", 0.0),
                    "uncertainty": uaor_scores.get("uncertainty", 0.0)
                }
            }
            
            self._append_jsonl(self.events_path, sgi_data)
            
            # Write individual track data
            for track in tracks:
                track_data = {
                    "ts": ts_sec,
                    "frame": frame_idx,
                    "track": track
                }
                self._append_jsonl(self.tracks_path, track_data)
                
        except Exception as e:
            logger.warning(f"Failed to write frame data: {e}")
            
    def _append_jsonl(self, path: Path, data: Dict[str, Any]):
        """Atomically append JSON line to file."""
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, 
                                           prefix=f".{path.name}.", 
                                           delete=False) as f:
                temp_path = Path(f.name)
                
                # If target exists, copy existing content
                if path.exists():
                    with open(path, 'r') as existing:
                        f.write(existing.read())
                        
                # Append new line
                f.write(json.dumps(data) + '\n')
                
            # Atomic rename
            temp_path.replace(path)
            
        except Exception as e:
            logger.warning(f"Failed to append to {path}: {e}")
            # Cleanup temp file if it exists
            try:
                if 'temp_path' in locals():
                    temp_path.unlink(missing_ok=True)
            except:
                pass