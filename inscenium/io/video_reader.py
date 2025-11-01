"""Video reading and writing utilities using OpenCV."""

import logging
from pathlib import Path
from typing import Iterator, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoReader:
    """Read video frames using cv2.VideoCapture with error tolerance."""
    
    def __init__(self, path: str, every_nth: int = 1, max_failures: int = 100):
        self.path = Path(path)
        self.every_nth = max(1, every_nth)
        self.max_failures = max_failures
        self._cap = None
        self._fps = None
        self._frame_count = None
        
    def __enter__(self):
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self.path}")
        
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._cap:
            self._cap.release()
            
    def frames(self) -> Iterator[Tuple[int, float, np.ndarray]]:
        """Yield (frame_idx, ts_sec, frame_bgr) tuples."""
        if not self._cap:
            raise RuntimeError("VideoReader not initialized")
            
        frame_idx = 0
        failures = 0
        
        while True:
            ret, frame = self._cap.read()
            if not ret:
                break
                
            if frame is None:
                failures += 1
                if failures >= self.max_failures:
                    logger.warning(f"Max failures ({self.max_failures}) reached, stopping")
                    break
                logger.warning(f"Failed to read frame {frame_idx}")
                frame_idx += 1
                continue
                
            if frame_idx % self.every_nth == 0:
                ts_sec = frame_idx / self._fps
                yield frame_idx, ts_sec, frame
                
            frame_idx += 1
            
    @property
    def fps(self) -> float:
        return self._fps or 30.0
        
    @property
    def frame_count(self) -> int:
        return self._frame_count or 0


class VideoWriter:
    """Write video frames using cv2.VideoWriter."""
    
    def __init__(self, path: str, fps: float, size: Tuple[int, int]):
        self.path = Path(path)
        self.fps = fps
        self.size = size
        self._writer = None
        
    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._writer = cv2.VideoWriter(str(self.path), fourcc, self.fps, self.size)
        if not self._writer.isOpened():
            raise RuntimeError(f"Cannot create video writer: {self.path}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._writer:
            self._writer.release()
            
    def write(self, frame: np.ndarray):
        """Write a BGR frame."""
        if self._writer:
            self._writer.write(frame)


def probe_video(path: str) -> dict:
    """Probe video file for basic properties."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"error": f"Cannot open video: {path}"}
        
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return {
            "fps": fps,
            "frames": frame_count,
            "width": width,
            "height": height,
            "duration_sec": frame_count / fps if fps > 0 else 0
        }
    finally:
        cap.release()