"""Object detection using torchvision or stub fallback."""

import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

# Global detector instance
_detector = None
_stub_logged = False


def _load_torchvision_detector():
    """Load torchvision FasterRCNN detector."""
    try:
        import torch
        import torchvision.transforms as transforms
        from torchvision.models import detection
        
        model = detection.fasterrcnn_resnet50_fpn(weights="DEFAULT")
        model.eval()
        
        # Move to CPU explicitly
        model = model.to("cpu")
        
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.ToTensor()
        ])
        
        # COCO class names (subset)
        class_names = [
            "background", "person", "bicycle", "car", "motorcycle", "airplane",
            "bus", "train", "truck", "boat", "traffic light", "fire hydrant",
            "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse",
            "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis",
            "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
            "skateboard", "surfboard", "tennis racket", "bottle", "wine glass",
            "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich",
            "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
            "chair", "couch", "potted plant", "bed", "dining table", "toilet",
            "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
            "microwave", "oven", "toaster", "sink", "refrigerator", "book",
            "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        ]
        
        return {"model": model, "transform": transform, "classes": class_names}
    except ImportError as e:
        logger.warning(f"torchvision not available: {e}")
        return None


def _get_detector():
    """Get or initialize detector."""
    global _detector, _stub_logged
    
    if _detector is None:
        _detector = _load_torchvision_detector()
        if _detector is None:
            _detector = "stub"
            if not _stub_logged:
                logger.info("Detector stub active.")
                _stub_logged = True
                
    return _detector


def detect(frame_bgr: np.ndarray, score_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Detect objects in BGR frame.
    
    Returns list of detections: [{"bbox": [x, y, w, h], "conf": float, "label": str}, ...]
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return []
        
    height, width = frame_bgr.shape[:2]
    detector = _get_detector()
    
    if detector == "stub":
        return []
        
    try:
        import torch
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Transform and add batch dimension
        input_tensor = detector["transform"](frame_rgb).unsqueeze(0)
        
        with torch.no_grad():
            predictions = detector["model"](input_tensor)[0]
            
        detections = []
        boxes = predictions["boxes"].cpu().numpy()
        scores = predictions["scores"].cpu().numpy()
        labels = predictions["labels"].cpu().numpy()
        
        for box, score, label in zip(boxes, scores, labels):
            if score >= score_threshold:
                x1, y1, x2, y2 = box
                
                # Clamp to image bounds
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(x1, min(x2, width))
                y2 = max(y1, min(y2, height))
                
                # Convert to [x, y, w, h]
                x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                
                if w > 0 and h > 0:  # Valid bbox
                    label_name = detector["classes"][label] if label < len(detector["classes"]) else f"class_{label}"
                    detections.append({
                        "bbox": [x, y, w, h],
                        "conf": float(score),
                        "label": label_name
                    })
                    
        return detections
        
    except Exception as e:
        logger.warning(f"Detection failed: {e}")
        return []


# Import cv2 if needed for color conversion
try:
    import cv2
except ImportError:
    logger.warning("opencv-python-headless not available")
    cv2 = None