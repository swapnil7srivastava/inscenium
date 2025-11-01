"""Metrics and performance tracking."""

import time
from typing import Dict, Any
from collections import defaultdict, deque


class Metrics:
    """Track pipeline metrics and performance."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.fps_window = deque(maxlen=100)
        self.stage_times = defaultdict(list)
        self.start_time = time.time()
        
    def increment(self, counter: str, value: int = 1):
        """Increment a counter."""
        self.counters[counter] += value
        
    def timer_start(self, name: str) -> float:
        """Start timing an operation."""
        return time.time()
        
    def timer_end(self, name: str, start_time: float):
        """End timing an operation."""
        duration = time.time() - start_time
        self.timers[name].append(duration)
        self.stage_times[name].append(duration)
        
        # Keep only recent measurements
        if len(self.stage_times[name]) > 1000:
            self.stage_times[name] = self.stage_times[name][-500:]
            
    def update_fps(self, frame_time: float):
        """Update FPS measurement."""
        self.fps_window.append(frame_time)
        
    def get_avg_fps(self) -> float:
        """Get average FPS from recent frames."""
        if not self.fps_window:
            return 0.0
            
        avg_time = sum(self.fps_window) / len(self.fps_window)
        return 1.0 / avg_time if avg_time > 0 else 0.0
        
    def get_stage_latencies(self) -> Dict[str, float]:
        """Get average latencies for each stage."""
        latencies = {}
        for stage, times in self.stage_times.items():
            if times:
                latencies[stage] = sum(times) / len(times)
        return latencies
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON export."""
        return {
            "runtime_sec": time.time() - self.start_time,
            "counters": dict(self.counters),
            "avg_fps": self.get_avg_fps(),
            "stage_latencies": self.get_stage_latencies(),
            "total_frames": self.counters.get("frames_processed", 0),
            "dropped_frames": self.counters.get("frames_dropped", 0),
            "detection_failures": self.counters.get("detection_failures", 0)
        }