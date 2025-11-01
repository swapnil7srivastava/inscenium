"""
Edge Processing for Inscenium
=============================

Real-time processing capabilities for edge deployment scenarios,
including lightweight models and optimized inference.
"""

import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import threading
from queue import Queue, Empty
import cv2

logger = logging.getLogger(__name__)

@dataclass
class EdgeConfig:
    """Configuration for edge processing"""
    max_resolution: Tuple[int, int] = (720, 1280)  # Max processing resolution
    target_fps: float = 30.0
    quality_preset: str = "balanced"  # fast, balanced, quality
    batch_size: int = 1
    memory_limit_mb: int = 512
    use_gpu_acceleration: bool = True
    enable_caching: bool = True
    processing_threads: int = 2

@dataclass
class ProcessingStats:
    """Processing performance statistics"""
    frames_processed: int = 0
    processing_time_ms: float = 0.0
    avg_fps: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    gpu_usage_percent: float = 0.0
    queue_depth: int = 0
    errors: int = 0

class EdgeProcessor:
    """Optimized edge processing for real-time Inscenium pipeline"""
    
    def __init__(self, config: Optional[EdgeConfig] = None):
        self.config = config or EdgeConfig()
        self.is_running = False
        self.stats = ProcessingStats()
        
        # Processing pipeline
        self.input_queue = Queue(maxsize=10)
        self.output_queue = Queue(maxsize=10) 
        self.processing_threads = []
        
        # Model cache
        self.model_cache = {}
        self.last_cleanup = time.time()
        
        # Performance monitoring
        self.frame_times = []
        self.max_frame_history = 100
        
        logger.info(f"Initialized edge processor with config: {self.config}")
    
    def start_processing(self) -> bool:
        """Start the edge processing pipeline"""
        try:
            if self.is_running:
                logger.warning("Edge processor already running")
                return True
            
            # Initialize lightweight models
            if not self._initialize_models():
                logger.error("Failed to initialize edge models")
                return False
            
            # Start processing threads
            self.is_running = True
            
            for i in range(self.config.processing_threads):
                thread = threading.Thread(
                    target=self._processing_worker,
                    name=f"EdgeProcessor-{i}",
                    daemon=True
                )
                thread.start()
                self.processing_threads.append(thread)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitoring_worker,
                name="EdgeMonitor",
                daemon=True
            )
            monitor_thread.start()
            
            logger.info("Edge processing pipeline started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start edge processor: {e}")
            return False
    
    def stop_processing(self):
        """Stop the edge processing pipeline"""
        try:
            self.is_running = False
            
            # Wait for threads to finish
            for thread in self.processing_threads:
                thread.join(timeout=5.0)
            
            # Clear queues
            self._clear_queue(self.input_queue)
            self._clear_queue(self.output_queue)
            
            logger.info("Edge processing pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping edge processor: {e}")
    
    def process_frame(self, frame: np.ndarray, metadata: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Process single frame through edge pipeline
        
        Args:
            frame: Input video frame (H, W, 3)
            metadata: Optional frame metadata
            
        Returns:
            Processing results or None if failed
        """
        try:
            if not self.is_running:
                logger.warning("Edge processor not running")
                return None
            
            # Prepare frame data
            frame_data = {
                "frame": frame,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "frame_id": self.stats.frames_processed
            }
            
            # Add to input queue (non-blocking)
            try:
                self.input_queue.put(frame_data, timeout=0.1)
                return {"status": "queued", "frame_id": frame_data["frame_id"]}
            except:
                logger.warning("Input queue full, dropping frame")
                return {"status": "dropped", "reason": "queue_full"}
                
        except Exception as e:
            logger.error(f"Frame processing failed: {e}")
            self.stats.errors += 1
            return None
    
    def get_results(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """Get processing results from output queue"""
        try:
            return self.output_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def _initialize_models(self) -> bool:
        """Initialize lightweight models for edge processing"""
        try:
            # Mock model initialization - would load actual lightweight models
            models_to_load = [
                ("surface_detector", "mobilenet_v2_surface"),
                ("depth_estimator", "midas_small"),
                ("quality_checker", "lightweight_qc")
            ]
            
            for model_name, model_path in models_to_load:
                # Mock model loading
                logger.info(f"Loading edge model: {model_name}")
                
                # Simulate model loading time
                time.sleep(0.1)
                
                # Cache mock model
                self.model_cache[model_name] = {
                    "model": f"mock_{model_name}",
                    "loaded_at": time.time(),
                    "input_size": (256, 256),  # Smaller for edge
                    "inference_time_ms": 15.0  # Optimized for speed
                }
            
            logger.info(f"Loaded {len(self.model_cache)} edge models")
            return True
            
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            return False
    
    def _processing_worker(self):
        """Worker thread for processing frames"""
        thread_id = threading.current_thread().name
        logger.debug(f"Started processing worker: {thread_id}")
        
        while self.is_running:
            try:
                # Get frame from input queue
                frame_data = self.input_queue.get(timeout=1.0)
                
                # Process frame
                start_time = time.time()
                result = self._process_frame_internal(frame_data)
                processing_time = (time.time() - start_time) * 1000
                
                # Add timing info
                result["processing_time_ms"] = processing_time
                result["worker_id"] = thread_id
                
                # Put result in output queue
                try:
                    self.output_queue.put(result, timeout=0.5)
                except:
                    logger.warning("Output queue full, dropping result")
                
                # Update stats
                self.stats.frames_processed += 1
                self._update_performance_stats(processing_time)
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {thread_id} error: {e}")
                self.stats.errors += 1
    
    def _process_frame_internal(self, frame_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal frame processing logic"""
        try:
            frame = frame_data["frame"]
            frame_id = frame_data["frame_id"]
            
            # Resize frame for edge processing
            resized_frame = self._resize_for_edge(frame)
            
            # Run lightweight pipeline
            results = {}
            
            # 1. Surface detection (lightweight)
            surfaces = self._detect_surfaces_light(resized_frame)
            results["surfaces"] = surfaces
            
            # 2. Quick depth estimation
            depth_map = self._estimate_depth_light(resized_frame)
            results["depth"] = depth_map
            
            # 3. Basic quality check
            quality_score = self._check_quality_light(resized_frame, surfaces)
            results["quality_score"] = quality_score
            
            # 4. Generate opportunities
            opportunities = self._generate_opportunities_light(surfaces, depth_map, quality_score)
            results["opportunities"] = opportunities
            
            return {
                "frame_id": frame_id,
                "timestamp": frame_data["timestamp"],
                "results": results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Internal processing failed: {e}")
            return {
                "frame_id": frame_data.get("frame_id", -1),
                "timestamp": frame_data.get("timestamp", time.time()),
                "results": {},
                "success": False,
                "error": str(e)
            }
    
    def _resize_for_edge(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame for edge processing constraints"""
        h, w = frame.shape[:2]
        max_h, max_w = self.config.max_resolution
        
        if h <= max_h and w <= max_w:
            return frame
        
        # Calculate scaling factor
        scale = min(max_h / h, max_w / w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    def _detect_surfaces_light(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Lightweight surface detection"""
        # Mock lightweight surface detection
        time.sleep(0.005)  # Simulate fast processing
        
        # Generate mock surfaces
        h, w = frame.shape[:2]
        surfaces = []
        
        for i in range(np.random.randint(0, 3)):  # 0-2 surfaces
            x = np.random.randint(0, w//2)
            y = np.random.randint(0, h//2)
            width = np.random.randint(50, w//3)
            height = np.random.randint(30, h//3)
            
            surface = {
                "surface_id": f"edge_surf_{i:03d}",
                "bbox": [x, y, x + width, y + height],
                "confidence": 0.7 + np.random.random() * 0.2,
                "surface_type": np.random.choice(["wall", "table", "screen"]),
                "area_pixels": width * height
            }
            surfaces.append(surface)
        
        return surfaces
    
    def _estimate_depth_light(self, frame: np.ndarray) -> Dict[str, Any]:
        """Lightweight depth estimation"""
        # Mock lightweight depth estimation
        time.sleep(0.008)  # Simulate fast processing
        
        h, w = frame.shape[:2]
        
        return {
            "depth_map_shape": (h, w),
            "mean_depth": 3.5 + np.random.random() * 2.0,
            "depth_range": [1.0, 8.0],
            "confidence": 0.6 + np.random.random() * 0.2
        }
    
    def _check_quality_light(self, frame: np.ndarray, surfaces: List[Dict]) -> float:
        """Lightweight quality assessment"""
        # Mock quality check
        time.sleep(0.003)
        
        base_quality = 60 + np.random.random() * 30
        
        # Bonus for detected surfaces
        surface_bonus = len(surfaces) * 5
        
        return min(100, base_quality + surface_bonus)
    
    def _generate_opportunities_light(self, 
                                    surfaces: List[Dict],
                                    depth_map: Dict[str, Any],
                                    quality_score: float) -> List[Dict[str, Any]]:
        """Generate placement opportunities from edge analysis"""
        opportunities = []
        
        for surface in surfaces:
            if surface["confidence"] > 0.6:  # Quality threshold for edge
                opportunity = {
                    "opportunity_id": f"edge_opp_{len(opportunities):03d}",
                    "surface_id": surface["surface_id"],
                    "prs_score": min(quality_score * surface["confidence"], 100),
                    "placement_type": surface["surface_type"],
                    "bbox": surface["bbox"],
                    "confidence": surface["confidence"],
                    "edge_processed": True
                }
                opportunities.append(opportunity)
        
        return opportunities
    
    def _monitoring_worker(self):
        """Monitor performance and system resources"""
        while self.is_running:
            try:
                # Update queue depths
                self.stats.queue_depth = self.input_queue.qsize()
                
                # Calculate average FPS
                if len(self.frame_times) > 0:
                    recent_times = self.frame_times[-30:]  # Last 30 frames
                    if len(recent_times) > 1:
                        time_diff = recent_times[-1] - recent_times[0]
                        self.stats.avg_fps = (len(recent_times) - 1) / time_diff if time_diff > 0 else 0
                
                # Mock system resource monitoring
                self.stats.memory_usage_mb = 128 + np.random.random() * 64
                self.stats.cpu_usage_percent = 30 + np.random.random() * 20
                self.stats.gpu_usage_percent = 15 + np.random.random() * 25
                
                # Cleanup old models if needed
                if time.time() - self.last_cleanup > 300:  # Every 5 minutes
                    self._cleanup_models()
                    self.last_cleanup = time.time()
                
                time.sleep(1.0)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    def _update_performance_stats(self, processing_time_ms: float):
        """Update performance statistics"""
        current_time = time.time()
        
        # Add to frame time history
        self.frame_times.append(current_time)
        if len(self.frame_times) > self.max_frame_history:
            self.frame_times.pop(0)
        
        # Update processing time (exponential moving average)
        alpha = 0.1
        self.stats.processing_time_ms = (
            alpha * processing_time_ms + 
            (1 - alpha) * self.stats.processing_time_ms
        )
    
    def _cleanup_models(self):
        """Clean up unused models to free memory"""
        try:
            current_time = time.time()
            cleanup_threshold = 1800  # 30 minutes
            
            models_to_remove = []
            for model_name, model_info in self.model_cache.items():
                if current_time - model_info["loaded_at"] > cleanup_threshold:
                    models_to_remove.append(model_name)
            
            for model_name in models_to_remove:
                del self.model_cache[model_name]
                logger.info(f"Cleaned up unused model: {model_name}")
                
        except Exception as e:
            logger.error(f"Model cleanup failed: {e}")
    
    def _clear_queue(self, queue: Queue):
        """Clear all items from a queue"""
        try:
            while True:
                queue.get_nowait()
        except Empty:
            pass
    
    def get_performance_stats(self) -> ProcessingStats:
        """Get current performance statistics"""
        return self.stats
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models"""
        return {
            "loaded_models": list(self.model_cache.keys()),
            "model_count": len(self.model_cache),
            "memory_per_model_mb": self.stats.memory_usage_mb / max(len(self.model_cache), 1)
        }
    
    def optimize_for_device(self, device_type: str = "cpu") -> bool:
        """Optimize processing for specific device type"""
        try:
            if device_type.lower() == "gpu":
                # Enable GPU optimizations
                self.config.use_gpu_acceleration = True
                self.config.batch_size = min(4, self.config.batch_size)
                self.config.quality_preset = "balanced"
            elif device_type.lower() == "mobile":
                # Mobile optimizations
                self.config.max_resolution = (480, 720)
                self.config.batch_size = 1
                self.config.quality_preset = "fast"
                self.config.memory_limit_mb = 256
            else:  # CPU
                # CPU optimizations
                self.config.use_gpu_acceleration = False
                self.config.processing_threads = min(2, self.config.processing_threads)
                self.config.quality_preset = "balanced"
            
            logger.info(f"Optimized for device type: {device_type}")
            return True
            
        except Exception as e:
            logger.error(f"Device optimization failed: {e}")
            return False

def create_edge_processor(config: Optional[EdgeConfig] = None) -> EdgeProcessor:
    """
    Create and configure edge processor
    
    Args:
        config: Edge processing configuration
        
    Returns:
        Configured EdgeProcessor instance
    """
    return EdgeProcessor(config)

# Mock edge processing for testing
def mock_edge_processing(frame_count: int, device_type: str = "cpu") -> Dict[str, Any]:
    """Generate mock edge processing results for CI testing"""
    return {
        "device_type": device_type,
        "frames_processed": frame_count,
        "avg_processing_time_ms": 18.5,
        "avg_fps": 32.1,
        "total_opportunities": frame_count * 2,
        "avg_prs_score": 72.3,
        "memory_usage_mb": 145.2,
        "cpu_usage_percent": 35.8,
        "gpu_usage_percent": 12.4 if device_type == "gpu" else 0.0,
        "model_optimization": "lightweight",
        "edge_efficiency": "high"
    }

if __name__ == "__main__":
    # Demo usage
    config = EdgeConfig(
        max_resolution=(480, 640),
        target_fps=30.0,
        quality_preset="fast",
        processing_threads=1
    )
    
    processor = EdgeProcessor(config)
    
    if processor.start_processing():
        print("Edge processor started successfully")
        
        # Process a few test frames
        for i in range(5):
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            result = processor.process_frame(test_frame, {"frame_id": i})
            print(f"Frame {i} processed: {result}")
            
            # Get results
            time.sleep(0.1)
            output = processor.get_results()
            if output:
                print(f"  Result: {output['success']}, Opportunities: {len(output['results'].get('opportunities', []))}")
        
        # Show performance stats
        stats = processor.get_performance_stats()
        print(f"Performance: {stats.avg_fps:.1f} FPS, {stats.processing_time_ms:.1f}ms avg")
        
        processor.stop_processing()
    else:
        print("Failed to start edge processor")