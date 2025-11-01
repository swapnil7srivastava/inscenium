"""Video overlay rendering and thumbnail generation."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    logger.warning("opencv-python-headless not available for rendering")
    HAS_CV2 = False


class OverlayRenderer:
    """Render tracking overlays on video frames."""
    
    def __init__(self, font_scale: float = 0.5, trails: bool = True, 
                 hud: bool = False, run_id: Optional[str] = None, profile: str = "cpu"):
        self.font_scale = font_scale
        self.trails = trails
        self.hud = hud
        self.run_id = run_id
        self.profile = profile
        self.track_trails = {}  # track_id -> list of centers
        self.colors = self._generate_colors()
        
    def _generate_colors(self) -> List[tuple]:
        """Generate distinct colors for tracks."""
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
            (128, 0, 128),  # Purple
            (255, 165, 0),  # Orange
            (0, 128, 128),  # Teal
            (128, 128, 0),  # Olive
        ]
        
        # Extend with more colors if needed
        for i in range(len(colors), 50):
            # Generate pseudo-random colors
            np.random.seed(i)
            color = tuple(np.random.randint(0, 256, 3).tolist())
            colors.append(color)
            
        return colors
        
    def _get_track_color(self, track_id: int) -> tuple:
        """Get consistent color for track ID."""
        return self.colors[track_id % len(self.colors)]
        
    def _draw_bbox(self, frame: np.ndarray, track: Dict[str, Any]) -> np.ndarray:
        """Draw bounding box and label for track."""
        if not HAS_CV2:
            return frame
            
        try:
            bbox = track["bbox"]
            track_id = track["id"]
            label = track.get("label", "object")
            conf = track.get("conf", 0.0)
            
            x, y, w, h = bbox
            color = self._get_track_color(track_id)
            
            # Draw bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label and info
            text = f"ID:{track_id} {label} {conf:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            thickness = 1
            
            # Get text size for background
            (text_w, text_h), baseline = cv2.getTextSize(text, font, self.font_scale, thickness)
            
            # Draw text background
            cv2.rectangle(frame, (x, y - text_h - 10), (x + text_w, y), color, -1)
            
            # Draw text
            cv2.putText(frame, text, (x, y - 5), font, self.font_scale, (255, 255, 255), thickness)
            
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to draw bbox: {e}")
            return frame
            
    def _draw_uaor_bars(self, frame: np.ndarray, uaor_scores: Dict[str, float]) -> np.ndarray:
        """Draw UAOR mini-bars in corner."""
        if not HAS_CV2:
            return frame
            
        try:
            h, w = frame.shape[:2]
            bar_width = 100
            bar_height = 10
            margin = 10
            
            # Occlusion bar (red)
            occlusion = uaor_scores.get("occlusion", 0.0)
            occ_len = int(bar_width * occlusion)
            cv2.rectangle(frame, (w - bar_width - margin, margin), 
                         (w - bar_width - margin + occ_len, margin + bar_height), 
                         (0, 0, 255), -1)
            cv2.rectangle(frame, (w - bar_width - margin, margin), 
                         (w - margin, margin + bar_height), (255, 255, 255), 1)
            cv2.putText(frame, "Occ", (w - bar_width - margin, margin + bar_height + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            
            # Uncertainty bar (yellow)
            uncertainty = uaor_scores.get("uncertainty", 0.0)
            unc_len = int(bar_width * uncertainty)
            cv2.rectangle(frame, (w - bar_width - margin, margin + 25), 
                         (w - bar_width - margin + unc_len, margin + 25 + bar_height), 
                         (0, 255, 255), -1)
            cv2.rectangle(frame, (w - bar_width - margin, margin + 25), 
                         (w - margin, margin + 25 + bar_height), (255, 255, 255), 1)
            cv2.putText(frame, "Unc", (w - bar_width - margin, margin + 25 + bar_height + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
                       
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to draw UAOR bars: {e}")
            return frame
            
    def _draw_trails(self, frame: np.ndarray, tracks: List[Dict[str, Any]]) -> np.ndarray:
        """Draw track trails."""
        if not HAS_CV2 or not self.trails:
            return frame
            
        try:
            for track in tracks:
                track_id = track["id"]
                bbox = track["bbox"]
                
                # Update trail
                center = (bbox[0] + bbox[2]//2, bbox[1] + bbox[3]//2)
                if track_id not in self.track_trails:
                    self.track_trails[track_id] = []
                    
                self.track_trails[track_id].append(center)
                
                # Keep only recent trail points
                if len(self.track_trails[track_id]) > 30:
                    self.track_trails[track_id] = self.track_trails[track_id][-30:]
                    
                # Draw trail
                if len(self.track_trails[track_id]) > 1:
                    color = self._get_track_color(track_id)
                    points = np.array(self.track_trails[track_id], dtype=np.int32)
                    cv2.polylines(frame, [points], False, color, 1)
                    
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to draw trails: {e}")
            return frame
            
    def render_frame(self, frame: np.ndarray, tracks: List[Dict[str, Any]], 
                    uaor_scores: Dict[str, float]) -> np.ndarray:
        """Render complete overlay on frame."""
        if frame is None:
            return frame
            
        # Make a copy to avoid modifying original
        overlay_frame = frame.copy()
        
        # Draw track bboxes and labels
        for track in tracks:
            overlay_frame = self._draw_bbox(overlay_frame, track)
            
        # Draw trails
        overlay_frame = self._draw_trails(overlay_frame, tracks)
        
        # Draw UAOR bars
        overlay_frame = self._draw_uaor_bars(overlay_frame, uaor_scores)
        
        # Draw HUD if enabled
        if self.hud:
            overlay_frame = self._draw_hud(overlay_frame)
        
        return overlay_frame
        
    def _draw_hud(self, frame: np.ndarray) -> np.ndarray:
        """Draw HUD overlay with app info."""
        if not HAS_CV2:
            return frame
            
        try:
            from datetime import datetime
            h, w = frame.shape[:2]
            
            # HUD background
            hud_height = 80
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, hud_height), (0, 0, 0), -1)
            cv2.addWeighted(frame, 0.7, overlay, 0.3, 0, frame)
            
            # App name and version
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Title
            cv2.putText(frame, "Inscenium v1.0.0", (10, 25), font, 0.6, (255, 255, 255), 2)
            
            # Run ID (short)
            run_text = f"Run: {self.run_id[:8] if self.run_id else 'N/A'}"
            cv2.putText(frame, run_text, (10, 45), font, 0.4, (200, 200, 200), 1)
            
            # Profile
            profile_text = f"Profile: {self.profile}"
            cv2.putText(frame, profile_text, (10, 65), font, 0.4, (200, 200, 200), 1)
            
            # Timestamp (right side)
            timestamp = datetime.now().strftime("%H:%M:%S")
            timestamp_size = cv2.getTextSize(timestamp, font, 0.5, 1)[0]
            cv2.putText(frame, timestamp, (w - timestamp_size[0] - 10, 25), font, 0.5, (255, 255, 255), 1)
            
            # Simple legend for track colors
            legend_y = 45
            cv2.putText(frame, "Tracks:", (w - 120, legend_y), font, 0.3, (200, 200, 200), 1)
            
            # Draw small colored squares for first few track colors
            for i, color in enumerate(self.colors[:5]):
                if i * 15 + (w - 80) < w - 10:
                    cv2.rectangle(frame, (w - 80 + i * 15, legend_y + 5), 
                                (w - 70 + i * 15, legend_y + 15), color, -1)
            
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to draw HUD: {e}")
            return frame
        
    def save_thumbnail(self, frame: np.ndarray, frame_idx: int, 
                      output_dir: Path, size: tuple = (320, 240)):
        """Save thumbnail of frame."""
        if not HAS_CV2:
            return
            
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Resize frame
            thumb = cv2.resize(frame, size)
            
            # Save as JPG
            thumb_path = output_dir / f"frame_{frame_idx:06d}.jpg"
            cv2.imwrite(str(thumb_path), thumb)
            
        except Exception as e:
            logger.warning(f"Failed to save thumbnail: {e}")