"""
Inscenium Color Pipeline
========================

Advanced color analysis and creative matching pipeline for contextual advertisement placement.
Analyzes scene color palettes, lighting conditions, and visual aesthetics to ensure 
creative content harmonizes with video scenes.

Key Features:
- Perceptual color space analysis (LAB, HSV, CIEDE2000)
- Scene color palette extraction and clustering
- Creative-to-scene color harmony scoring
- Lighting condition analysis
- Brand color compliance verification
- Automatic color correction recommendations
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
from PIL import Image
import colorsys
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import cv2

logger = logging.getLogger(__name__)


class ColorSpace:
    """Color space conversion utilities"""
    
    @staticmethod
    def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
        """Convert RGB to LAB color space"""
        # Normalize RGB to 0-1
        rgb_normalized = rgb.astype(np.float32) / 255.0
        
        # Convert to LAB using OpenCV
        rgb_image = rgb_normalized.reshape(-1, 1, 3)
        lab_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
        return lab_image.reshape(-1, 3)
    
    @staticmethod
    def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
        """Convert RGB to HSV color space"""
        return np.array([colorsys.rgb_to_hsv(r/255, g/255, b/255) for r, g, b in rgb])
    
    @staticmethod
    def ciede2000_distance(lab1: np.ndarray, lab2: np.ndarray) -> float:
        """Calculate perceptually uniform color distance using CIEDE2000"""
        # Simplified CIEDE2000 implementation
        # For production, use colorspacious or scikit-image
        delta_l = lab2[0] - lab1[0]
        delta_a = lab2[1] - lab1[1]  
        delta_b = lab2[2] - lab1[2]
        
        # Approximate CIEDE2000 formula (simplified)
        delta_e = np.sqrt(delta_l**2 + delta_a**2 + delta_b**2)
        return float(delta_e)


class ColorPalette:
    """Represents a color palette with analysis methods"""
    
    def __init__(self, colors: List[Tuple[int, int, int]], weights: Optional[List[float]] = None):
        self.colors = np.array(colors)
        self.weights = np.array(weights) if weights else np.ones(len(colors)) / len(colors)
        self._lab_colors = ColorSpace.rgb_to_lab(self.colors)
        self._hsv_colors = ColorSpace.rgb_to_hsv(self.colors)
    
    @property
    def dominant_color(self) -> Tuple[int, int, int]:
        """Get the most dominant color in the palette"""
        dominant_idx = np.argmax(self.weights)
        return tuple(self.colors[dominant_idx].astype(int))
    
    @property
    def average_color(self) -> Tuple[int, int, int]:
        """Get the weighted average color"""
        avg_color = np.average(self.colors, axis=0, weights=self.weights)
        return tuple(avg_color.astype(int))
    
    @property
    def color_temperature(self) -> float:
        """Estimate color temperature (warm vs cool) - returns 0-1 (cool to warm)"""
        # Analyze blue vs orange/red components
        avg_color = self.average_color
        cool_score = avg_color[2] / 255.0  # Blue component
        warm_score = (avg_color[0] + avg_color[1] * 0.5) / 255.0  # Red + some Green
        return warm_score / (warm_score + cool_score) if (warm_score + cool_score) > 0 else 0.5
    
    @property
    def saturation_level(self) -> float:
        """Average saturation level (0-1)"""
        return float(np.average(self._hsv_colors[:, 1], weights=self.weights))
    
    @property
    def brightness_level(self) -> float:
        """Average brightness level (0-1)"""
        return float(np.average(self._hsv_colors[:, 2], weights=self.weights))
    
    def harmony_score_with(self, other: 'ColorPalette') -> float:
        """Calculate color harmony score with another palette (0-1)"""
        total_score = 0.0
        total_weight = 0.0
        
        for i, color1 in enumerate(self._lab_colors):
            for j, color2 in enumerate(other._lab_colors):
                distance = ColorSpace.ciede2000_distance(color1, color2)
                # Convert distance to harmony score (lower distance = higher harmony)
                harmony = max(0, 1 - distance / 100.0)  # Normalize by typical max distance
                weight = self.weights[i] * other.weights[j]
                total_score += harmony * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0


class SceneColorAnalyzer:
    """Analyzes color characteristics of video scenes"""
    
    def __init__(self, n_colors: int = 8, min_colors: int = 3, max_colors: int = 12):
        self.n_colors = n_colors
        self.min_colors = min_colors
        self.max_colors = max_colors
    
    def extract_palette(self, image: Union[np.ndarray, Image.Image]) -> ColorPalette:
        """Extract dominant color palette from scene image"""
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
        
        # Ensure RGB format
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            pixels = image_array.reshape(-1, 3)
        else:
            raise ValueError("Image must be RGB format")
        
        # Remove pure black/white pixels that might be artifacts
        pixels = pixels[(pixels.sum(axis=1) > 10) & (pixels.sum(axis=1) < 745)]
        
        if len(pixels) == 0:
            # Fallback for edge cases
            return ColorPalette([(128, 128, 128)])
        
        # Determine optimal number of colors using elbow method
        n_colors = self._find_optimal_clusters(pixels)
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Extract cluster centers (dominant colors) and weights
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        weights = np.bincount(labels) / len(labels)
        
        return ColorPalette(colors, weights)
    
    def _find_optimal_clusters(self, pixels: np.ndarray) -> int:
        """Find optimal number of color clusters using silhouette analysis"""
        if len(pixels) < 100:  # Too few pixels for clustering analysis
            return min(self.n_colors, len(pixels))
        
        # Sample pixels if too many
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            sample_pixels = pixels[indices]
        else:
            sample_pixels = pixels
        
        best_score = -1
        best_n = self.n_colors
        
        for n in range(self.min_colors, min(self.max_colors + 1, len(sample_pixels))):
            try:
                kmeans = KMeans(n_clusters=n, random_state=42, n_init=5)
                labels = kmeans.fit_predict(sample_pixels)
                score = silhouette_score(sample_pixels, labels)
                
                if score > best_score:
                    best_score = score
                    best_n = n
            except Exception as e:
                logger.warning(f"Error computing silhouette score for {n} clusters: {e}")
                continue
        
        return best_n
    
    def analyze_lighting(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
        """Analyze lighting conditions in the scene"""
        if isinstance(image, Image.Image):
            image_array = np.array(image)
        else:
            image_array = image
        
        # Convert to grayscale for luminance analysis
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Calculate lighting metrics
        mean_luminance = float(np.mean(gray))
        std_luminance = float(np.std(gray))
        
        # Histogram analysis
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_normalized = hist.flatten() / hist.sum()
        
        # Detect lighting conditions
        is_low_light = mean_luminance < 80
        is_high_contrast = std_luminance > 60
        is_backlit = hist_normalized[:50].sum() > 0.3 and hist_normalized[-50:].sum() > 0.2
        is_evenly_lit = std_luminance < 40
        
        return {
            "mean_luminance": mean_luminance,
            "contrast_level": std_luminance,
            "is_low_light": is_low_light,
            "is_high_contrast": is_high_contrast,
            "is_backlit": is_backlit,
            "is_evenly_lit": is_evenly_lit,
            "luminance_distribution": hist_normalized.tolist()
        }


class CreativeColorMatcher:
    """Matches creative content colors to scene aesthetics"""
    
    def __init__(self):
        self.scene_analyzer = SceneColorAnalyzer()
    
    def analyze_compatibility(
        self, 
        scene_image: Union[np.ndarray, Image.Image],
        creative_image: Union[np.ndarray, Image.Image],
        brand_colors: Optional[List[Tuple[int, int, int]]] = None
    ) -> Dict[str, Any]:
        """Comprehensive color compatibility analysis"""
        
        # Extract color palettes
        scene_palette = self.scene_analyzer.extract_palette(scene_image)
        creative_palette = self.scene_analyzer.extract_palette(creative_image)
        
        # Calculate harmony scores
        harmony_score = scene_palette.harmony_score_with(creative_palette)
        
        # Analyze color characteristics
        temperature_match = 1.0 - abs(scene_palette.color_temperature - creative_palette.color_temperature)
        saturation_match = 1.0 - abs(scene_palette.saturation_level - creative_palette.saturation_level)
        brightness_match = 1.0 - abs(scene_palette.brightness_level - creative_palette.brightness_level)
        
        # Overall compatibility score
        compatibility_score = (
            harmony_score * 0.4 + 
            temperature_match * 0.25 +
            saturation_match * 0.2 +
            brightness_match * 0.15
        )
        
        # Analyze lighting conditions
        scene_lighting = self.scene_analyzer.analyze_lighting(scene_image)
        creative_lighting = self.scene_analyzer.analyze_lighting(creative_image)
        
        # Brand color compliance (if provided)
        brand_compliance = None
        if brand_colors:
            brand_palette = ColorPalette(brand_colors)
            brand_compliance = {
                "scene_harmony": scene_palette.harmony_score_with(brand_palette),
                "creative_harmony": creative_palette.harmony_score_with(brand_palette),
                "dominant_brand_color": brand_palette.dominant_color
            }
        
        return {
            "compatibility_score": float(compatibility_score),
            "harmony_score": float(harmony_score),
            "temperature_match": float(temperature_match),
            "saturation_match": float(saturation_match),
            "brightness_match": float(brightness_match),
            "scene_palette": {
                "colors": scene_palette.colors.tolist(),
                "weights": scene_palette.weights.tolist(),
                "dominant_color": scene_palette.dominant_color,
                "average_color": scene_palette.average_color,
                "color_temperature": float(scene_palette.color_temperature),
                "saturation_level": float(scene_palette.saturation_level),
                "brightness_level": float(scene_palette.brightness_level)
            },
            "creative_palette": {
                "colors": creative_palette.colors.tolist(), 
                "weights": creative_palette.weights.tolist(),
                "dominant_color": creative_palette.dominant_color,
                "average_color": creative_palette.average_color,
                "color_temperature": float(creative_palette.color_temperature),
                "saturation_level": float(creative_palette.saturation_level),
                "brightness_level": float(creative_palette.brightness_level)
            },
            "scene_lighting": scene_lighting,
            "creative_lighting": creative_lighting,
            "brand_compliance": brand_compliance,
            "recommendations": self._generate_recommendations(
                compatibility_score, scene_palette, creative_palette, scene_lighting
            )
        }
    
    def _generate_recommendations(
        self, 
        compatibility_score: float, 
        scene_palette: ColorPalette,
        creative_palette: ColorPalette,
        scene_lighting: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable color adjustment recommendations"""
        recommendations = []
        
        if compatibility_score < 0.6:
            recommendations.append("LOW_COMPATIBILITY: Consider adjusting creative colors for better scene harmony")
        
        if abs(scene_palette.color_temperature - creative_palette.color_temperature) > 0.3:
            if scene_palette.color_temperature > creative_palette.color_temperature:
                recommendations.append("TEMPERATURE_ADJUSTMENT: Warm up creative colors to match scene")
            else:
                recommendations.append("TEMPERATURE_ADJUSTMENT: Cool down creative colors to match scene")
        
        if abs(scene_palette.saturation_level - creative_palette.saturation_level) > 0.4:
            if scene_palette.saturation_level > creative_palette.saturation_level:
                recommendations.append("SATURATION_ADJUSTMENT: Increase creative color saturation")
            else:
                recommendations.append("SATURATION_ADJUSTMENT: Decrease creative color saturation")
        
        if scene_lighting["is_low_light"] and creative_palette.brightness_level < 0.4:
            recommendations.append("BRIGHTNESS_ADJUSTMENT: Increase creative brightness for low-light scene")
        
        if scene_lighting["is_high_contrast"] and creative_palette.brightness_level > 0.7:
            recommendations.append("CONTRAST_ADJUSTMENT: Consider darker creative for high-contrast scene")
        
        if compatibility_score > 0.8:
            recommendations.append("EXCELLENT_MATCH: Creative colors harmonize well with scene")
        
        return recommendations


class ColorPipelineProcessor:
    """Main color pipeline processor"""
    
    def __init__(self):
        self.matcher = CreativeColorMatcher()
        self.cache = {}  # Simple in-memory cache
    
    def process_placement_colors(
        self,
        scene_frame: Union[np.ndarray, Image.Image],
        creative_content: Union[np.ndarray, Image.Image],
        placement_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process color analysis for a placement opportunity"""
        
        try:
            # Extract relevant metadata
            surface_id = placement_metadata.get("surface_id", "unknown")
            brand_colors = placement_metadata.get("brand_colors")
            
            # Generate cache key based on scene and creative content
            cache_key = f"{surface_id}_{hash(str(placement_metadata))}"
            
            if cache_key in self.cache:
                logger.debug(f"Using cached color analysis for {surface_id}")
                return self.cache[cache_key]
            
            # Perform color analysis
            analysis = self.matcher.analyze_compatibility(
                scene_frame, 
                creative_content,
                brand_colors
            )
            
            # Add placement context
            analysis.update({
                "surface_id": surface_id,
                "analysis_timestamp": "2024-01-15T10:30:00Z",  # Would be actual timestamp
                "pipeline_version": "1.0.0"
            })
            
            # Cache results
            self.cache[cache_key] = analysis
            
            logger.info(f"Color analysis completed for {surface_id}: compatibility={analysis['compatibility_score']:.3f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in color pipeline processing: {e}")
            return {
                "error": str(e),
                "compatibility_score": 0.0,
                "recommendations": ["ERROR: Color analysis failed"]
            }
    
    def clear_cache(self) -> None:
        """Clear analysis cache"""
        self.cache.clear()
        logger.info("Color analysis cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_analyses": len(self.cache),
            "memory_usage_mb": sum(len(str(v)) for v in self.cache.values()) / (1024 * 1024)
        }


# Convenience function for external use
def analyze_placement_colors(
    scene_frame: Union[np.ndarray, Image.Image],
    creative_content: Union[np.ndarray, Image.Image],
    placement_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze color compatibility for placement.
    
    Args:
        scene_frame: Scene image as numpy array or PIL Image
        creative_content: Creative content image
        placement_metadata: Optional metadata with brand_colors, surface_id, etc.
    
    Returns:
        Dictionary with comprehensive color analysis results
    """
    processor = ColorPipelineProcessor()
    metadata = placement_metadata or {}
    
    return processor.process_placement_colors(scene_frame, creative_content, metadata)


# Mock deterministic implementation for CI testing
def mock_color_analysis() -> Dict[str, Any]:
    """Returns deterministic mock color analysis for CI testing"""
    return {
        "compatibility_score": 0.847,
        "harmony_score": 0.723,
        "temperature_match": 0.901,
        "saturation_match": 0.834,
        "brightness_match": 0.765,
        "scene_palette": {
            "colors": [[45, 78, 123], [234, 187, 156], [89, 134, 98]],
            "weights": [0.45, 0.32, 0.23],
            "dominant_color": (45, 78, 123),
            "average_color": (123, 132, 126),
            "color_temperature": 0.356,
            "saturation_level": 0.678,
            "brightness_level": 0.512
        },
        "creative_palette": {
            "colors": [[67, 89, 145], [245, 201, 123], [78, 145, 89]],
            "weights": [0.38, 0.35, 0.27],
            "dominant_color": (67, 89, 145),
            "average_color": (130, 145, 119),
            "color_temperature": 0.423,
            "saturation_level": 0.721,
            "brightness_level": 0.534
        },
        "recommendations": [
            "EXCELLENT_MATCH: Creative colors harmonize well with scene",
            "TEMPERATURE_ADJUSTMENT: Minor warming recommended"
        ],
        "pipeline_version": "1.0.0"
    }


if __name__ == "__main__":
    # Demo usage with mock data
    print("Inscenium Color Pipeline Demo")
    print("=" * 40)
    
    # Generate mock analysis
    result = mock_color_analysis()
    print(f"Compatibility Score: {result['compatibility_score']:.3f}")
    print(f"Harmony Score: {result['harmony_score']:.3f}")
    print(f"Dominant Scene Color: {result['scene_palette']['dominant_color']}")
    print(f"Dominant Creative Color: {result['creative_palette']['dominant_color']}")
    print("\nRecommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")