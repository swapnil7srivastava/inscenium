"""Simple BYTE-like tracker using IoU matching."""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


def iou(bbox1, bbox2):
    """Calculate IoU between two bboxes in [x, y, w, h] format."""
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
    area2 = w2 * h2
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def center(bbox):
    """Get center point of bbox [x, y, w, h]."""
    x, y, w, h = bbox
    return (x + w/2, y + h/2)


class Track:
    """Individual track state."""
    
    def __init__(self, track_id: int, detection: Dict[str, Any]):
        self.track_id = track_id
        self.bbox = detection["bbox"]
        self.label = detection["label"]
        self.conf = detection["conf"]
        self.age = 1
        self.lost_count = 0
        self.last_conf = detection["conf"]
        self.bbox_history = [detection["bbox"]]
        
    def update(self, detection: Dict[str, Any]):
        """Update track with new detection."""
        old_center = center(self.bbox)
        new_center = center(detection["bbox"])
        
        self.bbox = detection["bbox"]
        self.conf = detection["conf"]
        self.last_conf = detection["conf"]
        self.age += 1
        self.lost_count = 0
        self.bbox_history.append(detection["bbox"])
        
        # Keep only recent history
        if len(self.bbox_history) > 30:
            self.bbox_history = self.bbox_history[-30:]
            
    def predict(self):
        """Predict next position (simple: no motion model)."""
        self.age += 1
        self.lost_count += 1
        
    @property
    def bbox_jitter(self) -> float:
        """Calculate bbox jitter based on history."""
        if len(self.bbox_history) < 2:
            return 0.0
            
        centers = [center(bbox) for bbox in self.bbox_history[-10:]]
        if len(centers) < 2:
            return 0.0
            
        # Calculate variance in center positions
        x_coords = [c[0] for c in centers]
        y_coords = [c[1] for c in centers]
        
        x_var = np.var(x_coords) if len(x_coords) > 1 else 0.0
        y_var = np.var(y_coords) if len(y_coords) > 1 else 0.0
        
        return min(1.0, (x_var + y_var) / 1000.0)  # Normalize roughly
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary."""
        return {
            "id": self.track_id,
            "bbox": self.bbox,
            "label": self.label,
            "conf": self.conf,
            "age": self.age,
            "lost": self.lost_count,
            "jitter": self.bbox_jitter
        }


class ByteTracker:
    """Simple BYTE-like tracker."""
    
    def __init__(self, max_age: int = 30, iou_thresh: float = 0.3):
        self.max_age = max_age
        self.iou_thresh = iou_thresh
        self.tracks = []
        self.next_id = 1
        
    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Update tracker with new detections."""
        if not detections:
            # No detections, age existing tracks
            for track in self.tracks:
                track.predict()
            self._remove_old_tracks()
            return [track.to_dict() for track in self.tracks]
            
        # Match detections to existing tracks
        matched_tracks = []
        matched_dets = set()
        
        # Simple greedy matching based on IoU
        for track in self.tracks:
            best_iou = 0.0
            best_det_idx = -1
            
            for i, det in enumerate(detections):
                if i in matched_dets:
                    continue
                    
                iou_val = iou(track.bbox, det["bbox"])
                if iou_val > best_iou and iou_val > self.iou_thresh:
                    best_iou = iou_val
                    best_det_idx = i
                    
            if best_det_idx >= 0:
                track.update(detections[best_det_idx])
                matched_tracks.append(track)
                matched_dets.add(best_det_idx)
            else:
                track.predict()
                if track.lost_count <= self.max_age:
                    matched_tracks.append(track)
                    
        # Create new tracks for unmatched detections
        for i, det in enumerate(detections):
            if i not in matched_dets:
                new_track = Track(self.next_id, det)
                matched_tracks.append(new_track)
                self.next_id += 1
                
        self.tracks = matched_tracks
        self._remove_old_tracks()
        
        return [track.to_dict() for track in self.tracks]
        
    def _remove_old_tracks(self):
        """Remove tracks that are too old."""
        self.tracks = [t for t in self.tracks if t.lost_count <= self.max_age]