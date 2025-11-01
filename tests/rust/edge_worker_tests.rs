// Edge Worker WASM Tests for Inscenium
// Tests compilation and basic functionality of the edge compositing WASM module

use wasm_bindgen_test::*;

// Mock structures for testing
#[derive(Clone)]
pub struct VideoFrame {
    pub width: u32,
    pub height: u32,
    pub data: Vec<u8>,
}

#[derive(Clone)]
pub struct PlacementLayer {
    pub creative_data: Vec<u8>,
    pub transform: [f32; 9], // 3x3 transformation matrix
    pub opacity: f32,
    pub blend_mode: BlendMode,
}

#[derive(Clone)]
pub enum BlendMode {
    Normal,
    Multiply,
    Screen,
    Overlay,
}

pub struct CompositorConfig {
    pub max_memory_mb: u32,
    pub quality_threshold: f32,
    pub uncertainty_threshold: f32,
}

// Mock edge compositor implementation
pub struct EdgeCompositor {
    config: CompositorConfig,
    performance_stats: PerformanceStats,
}

#[derive(Default)]
pub struct PerformanceStats {
    pub frames_processed: u32,
    pub avg_processing_time_ms: f32,
    pub memory_usage_mb: f32,
    pub uncertainty_rejections: u32,
}

#[derive(Debug, PartialEq)]
pub enum CompositorError {
    InvalidInput,
    MemoryExceeded,
    UncertaintyThresholdExceeded,
    ProcessingFailed,
}

impl EdgeCompositor {
    pub fn new(config: CompositorConfig) -> Self {
        Self {
            config,
            performance_stats: PerformanceStats::default(),
        }
    }

    pub fn composite_segment(
        &mut self,
        base_frame: &VideoFrame,
        layers: &[PlacementLayer],
        uncertainty_score: f32,
    ) -> Result<VideoFrame, CompositorError> {
        // Validate inputs
        if base_frame.data.is_empty() {
            return Err(CompositorError::InvalidInput);
        }

        // Check uncertainty threshold
        if uncertainty_score > self.config.uncertainty_threshold {
            self.performance_stats.uncertainty_rejections += 1;
            return Err(CompositorError::UncertaintyThresholdExceeded);
        }

        // Check memory constraints
        let estimated_memory = self.estimate_memory_usage(base_frame, layers);
        if estimated_memory > self.config.max_memory_mb {
            return Err(CompositorError::MemoryExceeded);
        }

        // Perform compositing (mock implementation)
        let mut output_frame = base_frame.clone();

        for layer in layers {
            if self.should_composite_layer(layer, uncertainty_score) {
                self.composite_layer(&mut output_frame, layer)?;
            }
        }

        // Update performance stats
        self.performance_stats.frames_processed += 1;
        self.performance_stats.memory_usage_mb = estimated_memory as f32;

        Ok(output_frame)
    }

    fn estimate_memory_usage(&self, base_frame: &VideoFrame, layers: &[PlacementLayer]) -> u32 {
        let base_memory = (base_frame.width * base_frame.height * 4) / (1024 * 1024); // RGBA bytes to MB
        let layers_memory = layers.len() as u32 * 2; // Approximate 2MB per layer
        base_memory + layers_memory
    }

    fn should_composite_layer(&self, layer: &PlacementLayer, uncertainty: f32) -> bool {
        // Quality-based gating
        if layer.opacity < 0.1 {
            return false;
        }

        // Uncertainty-based gating for geometric transformations
        let transform_uncertainty = self.calculate_transform_uncertainty(&layer.transform, uncertainty);
        transform_uncertainty < self.config.quality_threshold
    }

    fn calculate_transform_uncertainty(&self, transform: &[f32; 9], base_uncertainty: f32) -> f32 {
        // Mock implementation - calculate uncertainty in geometric transformation
        let scale_x = transform[0];
        let scale_y = transform[4];
        let translation_uncertainty = (transform[2].abs() + transform[5].abs()) * base_uncertainty;
        let scale_uncertainty = ((scale_x - 1.0).abs() + (scale_y - 1.0).abs()) * base_uncertainty;
        
        translation_uncertainty + scale_uncertainty
    }

    fn composite_layer(&mut self, base_frame: &mut VideoFrame, layer: &PlacementLayer) -> Result<(), CompositorError> {
        // Mock compositing implementation
        if layer.creative_data.is_empty() {
            return Err(CompositorError::ProcessingFailed);
        }

        // Simulate compositing work
        match layer.blend_mode {
            BlendMode::Normal => self.blend_normal(base_frame, layer),
            BlendMode::Multiply => self.blend_multiply(base_frame, layer),
            BlendMode::Screen => self.blend_screen(base_frame, layer),
            BlendMode::Overlay => self.blend_overlay(base_frame, layer),
        }

        Ok(())
    }

    fn blend_normal(&mut self, base_frame: &mut VideoFrame, layer: &PlacementLayer) {
        // Mock normal blend implementation
        for i in 0..std::cmp::min(base_frame.data.len(), layer.creative_data.len()) {
            if i % 4 == 3 { // Alpha channel
                base_frame.data[i] = ((base_frame.data[i] as f32 * (1.0 - layer.opacity)) + 
                                     (layer.creative_data[i] as f32 * layer.opacity)) as u8;
            }
        }
    }

    fn blend_multiply(&mut self, _base_frame: &mut VideoFrame, _layer: &PlacementLayer) {
        // Mock multiply blend implementation
    }

    fn blend_screen(&mut self, _base_frame: &mut VideoFrame, _layer: &PlacementLayer) {
        // Mock screen blend implementation  
    }

    fn blend_overlay(&mut self, _base_frame: &mut VideoFrame, _layer: &PlacementLayer) {
        // Mock overlay blend implementation
    }

    pub fn get_performance_stats(&self) -> &PerformanceStats {
        &self.performance_stats
    }

    pub fn reset_stats(&mut self) {
        self.performance_stats = PerformanceStats::default();
    }
}

// WASM bindings configuration for testing
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn test_edge_compositor_creation() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let compositor = EdgeCompositor::new(config);
    assert_eq!(compositor.performance_stats.frames_processed, 0);
    assert_eq!(compositor.performance_stats.uncertainty_rejections, 0);
}

#[wasm_bindgen_test]
fn test_composite_segment_basic() {
    let mut config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    // Create test frame
    let base_frame = VideoFrame {
        width: 640,
        height: 480,
        data: vec![128u8; 640 * 480 * 4], // RGBA
    };

    // Create test layer
    let layer = PlacementLayer {
        creative_data: vec![255u8; 1000],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], // Identity matrix
        opacity: 0.8,
        blend_mode: BlendMode::Normal,
    };

    // Test compositing with low uncertainty
    let result = compositor.composite_segment(&base_frame, &[layer], 0.3);
    assert!(result.is_ok());

    let stats = compositor.get_performance_stats();
    assert_eq!(stats.frames_processed, 1);
    assert_eq!(stats.uncertainty_rejections, 0);
}

#[wasm_bindgen_test]
fn test_uncertainty_gating() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.5, // Lower threshold
    };

    let mut compositor = EdgeCompositor::new(config);

    let base_frame = VideoFrame {
        width: 320,
        height: 240,
        data: vec![100u8; 320 * 240 * 4],
    };

    let layer = PlacementLayer {
        creative_data: vec![200u8; 500],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.9,
        blend_mode: BlendMode::Normal,
    };

    // Test with high uncertainty (should be rejected)
    let result = compositor.composite_segment(&base_frame, &[layer.clone()], 0.8);
    assert_eq!(result.err(), Some(CompositorError::UncertaintyThresholdExceeded));

    let stats = compositor.get_performance_stats();
    assert_eq!(stats.uncertainty_rejections, 1);

    // Test with low uncertainty (should succeed)
    let result = compositor.composite_segment(&base_frame, &[layer], 0.3);
    assert!(result.is_ok());
}

#[wasm_bindgen_test]
fn test_memory_constraint_handling() {
    let config = CompositorConfig {
        max_memory_mb: 1, // Very low memory limit
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    // Create large frame that exceeds memory limit
    let base_frame = VideoFrame {
        width: 1920,
        height: 1080,
        data: vec![150u8; 1920 * 1080 * 4],
    };

    let layer = PlacementLayer {
        creative_data: vec![180u8; 2000],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.7,
        blend_mode: BlendMode::Normal,
    };

    let result = compositor.composite_segment(&base_frame, &[layer], 0.2);
    assert_eq!(result.err(), Some(CompositorError::MemoryExceeded));
}

#[wasm_bindgen_test]
fn test_invalid_input_handling() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    // Test with empty frame data
    let empty_frame = VideoFrame {
        width: 640,
        height: 480,
        data: vec![], // Empty data
    };

    let layer = PlacementLayer {
        creative_data: vec![200u8; 1000],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.8,
        blend_mode: BlendMode::Normal,
    };

    let result = compositor.composite_segment(&empty_frame, &[layer], 0.3);
    assert_eq!(result.err(), Some(CompositorError::InvalidInput));
}

#[wasm_bindgen_test]
fn test_multiple_blend_modes() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    let base_frame = VideoFrame {
        width: 400,
        height: 300,
        data: vec![120u8; 400 * 300 * 4],
    };

    let layers = vec![
        PlacementLayer {
            creative_data: vec![255u8; 800],
            transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            opacity: 0.6,
            blend_mode: BlendMode::Normal,
        },
        PlacementLayer {
            creative_data: vec![128u8; 600],
            transform: [0.8, 0.0, 10.0, 0.0, 0.8, 15.0, 0.0, 0.0, 1.0],
            opacity: 0.7,
            blend_mode: BlendMode::Multiply,
        },
        PlacementLayer {
            creative_data: vec![200u8; 400],
            transform: [1.2, 0.0, -5.0, 0.0, 1.2, -8.0, 0.0, 0.0, 1.0],
            opacity: 0.5,
            blend_mode: BlendMode::Screen,
        },
    ];

    let result = compositor.composite_segment(&base_frame, &layers, 0.4);
    assert!(result.is_ok());

    let stats = compositor.get_performance_stats();
    assert_eq!(stats.frames_processed, 1);
}

#[wasm_bindgen_test]
fn test_performance_statistics() {
    let config = CompositorConfig {
        max_memory_mb: 512,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    let base_frame = VideoFrame {
        width: 800,
        height: 600,
        data: vec![100u8; 800 * 600 * 4],
    };

    let layer = PlacementLayer {
        creative_data: vec![180u8; 1200],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.8,
        blend_mode: BlendMode::Normal,
    };

    // Process multiple frames
    for _ in 0..5 {
        let _ = compositor.composite_segment(&base_frame, &[layer.clone()], 0.3);
    }

    // Test high uncertainty rejection
    let _ = compositor.composite_segment(&base_frame, &[layer], 0.9);

    let stats = compositor.get_performance_stats();
    assert_eq!(stats.frames_processed, 5);
    assert_eq!(stats.uncertainty_rejections, 1);
    assert!(stats.memory_usage_mb > 0.0);
}

#[wasm_bindgen_test]
fn test_quality_based_layer_filtering() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.5,
        uncertainty_threshold: 0.8,
    };

    let compositor = EdgeCompositor::new(config);

    // Test layer with very low opacity (should be filtered out)
    let low_opacity_layer = PlacementLayer {
        creative_data: vec![255u8; 500],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.05, // Very low opacity
        blend_mode: BlendMode::Normal,
    };

    let should_composite = compositor.should_composite_layer(&low_opacity_layer, 0.3);
    assert!(!should_composite);

    // Test layer with good opacity
    let good_layer = PlacementLayer {
        creative_data: vec![255u8; 500],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.8,
        blend_mode: BlendMode::Normal,
    };

    let should_composite = compositor.should_composite_layer(&good_layer, 0.3);
    assert!(should_composite);
}

#[wasm_bindgen_test]
fn test_transform_uncertainty_calculation() {
    let config = CompositorConfig {
        max_memory_mb: 256,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let compositor = EdgeCompositor::new(config);

    // Identity transform (no uncertainty)
    let identity_transform = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0];
    let uncertainty = compositor.calculate_transform_uncertainty(&identity_transform, 0.5);
    assert!(uncertainty < 0.1);

    // Transform with scaling and translation (higher uncertainty)
    let complex_transform = [2.0, 0.0, 100.0, 0.0, 1.5, 50.0, 0.0, 0.0, 1.0];
    let uncertainty = compositor.calculate_transform_uncertainty(&complex_transform, 0.5);
    assert!(uncertainty > 0.1);
}

#[wasm_bindgen_test] 
fn test_wasm_memory_management() {
    let config = CompositorConfig {
        max_memory_mb: 128,
        quality_threshold: 0.8,
        uncertainty_threshold: 0.7,
    };

    let mut compositor = EdgeCompositor::new(config);

    // Test processing many frames without memory leaks
    let base_frame = VideoFrame {
        width: 320,
        height: 240,
        data: vec![50u8; 320 * 240 * 4],
    };

    let layer = PlacementLayer {
        creative_data: vec![100u8; 500],
        transform: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        opacity: 0.7,
        blend_mode: BlendMode::Normal,
    };

    // Process many frames
    for i in 0..20 {
        let result = compositor.composite_segment(&base_frame, &[layer.clone()], 0.2);
        assert!(result.is_ok(), "Frame {} failed to process", i);
    }

    let stats = compositor.get_performance_stats();
    assert_eq!(stats.frames_processed, 20);
    assert!(stats.memory_usage_mb < 128.0); // Should stay within limits
}