//! Inscenium Edge Worker - WebAssembly compositor

use wasm_bindgen::prelude::*;

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

/// Depth-aware alpha blending of creative content onto base frame
#[wasm_bindgen]
pub fn composite_segment(
    base_frame: &[u8],
    creative_frame: &[u8], 
    depth_map: &[f32],
    alpha_mask: &[u8],
    width: u32,
    height: u32,
    creative_depth: f32,
) -> Vec<u8> {
    log("WASM compositor: Processing frame");
    
    // Validate input parameters
    let pixel_count = (width * height) as usize;
    if base_frame.len() < pixel_count * 4 || 
       creative_frame.len() < pixel_count * 4 ||
       depth_map.len() < pixel_count ||
       alpha_mask.len() < pixel_count {
        log("WASM compositor: Invalid input buffer sizes");
        return base_frame.to_vec();
    }
    
    // Perform depth-aware compositing
    composite_with_depth(base_frame, creative_frame, depth_map, alpha_mask, width, height, creative_depth)
}

/// Internal compositing logic with depth testing
fn composite_with_depth(
    base_frame: &[u8],
    creative_frame: &[u8],
    depth_map: &[f32],
    alpha_mask: &[u8],
    width: u32,
    height: u32,
    creative_depth: f32,
) -> Vec<u8> {
    let pixel_count = (width * height) as usize;
    let mut result = vec![0u8; base_frame.len()];
    
    for i in 0..pixel_count {
        let pixel_idx = i * 4; // RGBA
        let scene_depth = depth_map[i];
        let alpha = alpha_mask[i] as f32 / 255.0;
        
        // Only composite if creative is in front of scene geometry
        if creative_depth < scene_depth && alpha > 0.0 {
            // Alpha blending: result = creative * alpha + base * (1 - alpha)
            for channel in 0..4 {
                let base_val = base_frame[pixel_idx + channel] as f32;
                let creative_val = creative_frame[pixel_idx + channel] as f32;
                let blended = creative_val * alpha + base_val * (1.0 - alpha);
                result[pixel_idx + channel] = blended.clamp(0.0, 255.0) as u8;
            }
        } else {
            // Use base frame pixel
            for channel in 0..4 {
                result[pixel_idx + channel] = base_frame[pixel_idx + channel];
            }
        }
    }
    
    result
}

/// Utility function to validate frame dimensions
#[wasm_bindgen]
pub fn validate_frame_size(data_len: usize, width: u32, height: u32) -> bool {
    data_len >= (width * height * 4) as usize
}

/// Get WebAssembly module version info
#[wasm_bindgen]
pub fn get_version_info() -> String {
    format!(
        "Inscenium Edge Worker WASM v{} - Built with Rust {}",
        env!("CARGO_PKG_VERSION"),
        env!("RUSTC_VERSION", "unknown")
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_frame_size() {
        // Valid RGBA frame for 100x100 image
        assert_eq!(validate_frame_size(40000, 100, 100), true);
        
        // Too small buffer
        assert_eq!(validate_frame_size(39999, 100, 100), false);
        
        // Edge cases
        assert_eq!(validate_frame_size(0, 0, 0), true);
        assert_eq!(validate_frame_size(4, 1, 1), true);
    }

    #[test]
    fn test_composite_with_depth_basic() {
        let width = 2;
        let height = 2;
        let pixel_count = 4;
        
        // Base frame: all red pixels
        let base_frame = vec![255u8, 0, 0, 255; pixel_count];
        
        // Creative frame: all blue pixels  
        let creative_frame = vec![0u8, 0, 255, 255; pixel_count];
        
        // Depth map: creative is in front (lower depth)
        let depth_map = vec![10.0f32; pixel_count];
        
        // Full alpha
        let alpha_mask = vec![255u8; pixel_count];
        
        let creative_depth = 5.0;
        
        let result = composite_with_depth(
            &base_frame,
            &creative_frame, 
            &depth_map,
            &alpha_mask,
            width,
            height,
            creative_depth
        );
        
        // Should be all blue (creative) since creative is in front
        for i in 0..pixel_count {
            let pixel_idx = i * 4;
            assert_eq!(result[pixel_idx], 0);     // R
            assert_eq!(result[pixel_idx + 1], 0); // G  
            assert_eq!(result[pixel_idx + 2], 255); // B
            assert_eq!(result[pixel_idx + 3], 255); // A
        }
    }

    #[test]
    fn test_composite_with_depth_behind() {
        let width = 2;
        let height = 2;
        let pixel_count = 4;
        
        // Base frame: all red pixels
        let base_frame = vec![255u8, 0, 0, 255; pixel_count];
        
        // Creative frame: all blue pixels
        let creative_frame = vec![0u8, 0, 255, 255; pixel_count];
        
        // Depth map: creative is behind (higher depth)
        let depth_map = vec![5.0f32; pixel_count];
        
        // Full alpha
        let alpha_mask = vec![255u8; pixel_count];
        
        let creative_depth = 10.0;
        
        let result = composite_with_depth(
            &base_frame,
            &creative_frame,
            &depth_map,
            &alpha_mask,
            width,
            height,
            creative_depth
        );
        
        // Should be all red (base) since creative is behind
        for i in 0..pixel_count {
            let pixel_idx = i * 4;
            assert_eq!(result[pixel_idx], 255);   // R
            assert_eq!(result[pixel_idx + 1], 0); // G
            assert_eq!(result[pixel_idx + 2], 0); // B
            assert_eq!(result[pixel_idx + 3], 255); // A
        }
    }

    #[test]
    fn test_composite_with_partial_alpha() {
        let width = 1;
        let height = 1;
        let pixel_count = 1;
        
        // Base frame: red pixel
        let base_frame = vec![255u8, 0, 0, 255];
        
        // Creative frame: blue pixel
        let creative_frame = vec![0u8, 0, 255, 255];
        
        // Creative is in front
        let depth_map = vec![10.0f32];
        
        // Half alpha
        let alpha_mask = vec![128u8]; // 50% alpha
        
        let creative_depth = 5.0;
        
        let result = composite_with_depth(
            &base_frame,
            &creative_frame,
            &depth_map,
            &alpha_mask,
            width,
            height,
            creative_depth
        );
        
        // Should be blended: 50% blue + 50% red
        // R: 0 * 0.5 + 255 * 0.5 = 127.5 ≈ 128
        // G: 0 * 0.5 + 0 * 0.5 = 0
        // B: 255 * 0.5 + 0 * 0.5 = 127.5 ≈ 128
        // A: 255 * 0.5 + 255 * 0.5 = 255
        assert_eq!(result[0], 128); // R
        assert_eq!(result[1], 0);   // G
        assert_eq!(result[2], 128); // B
        assert_eq!(result[3], 255); // A
    }

    #[test]
    fn test_composite_segment_invalid_input() {
        let width = 2;
        let height = 2;
        
        let base_frame = vec![255u8, 0, 0, 255];  // Too small
        let creative_frame = vec![0u8, 0, 255, 255; 4];
        let depth_map = vec![10.0f32; 4];
        let alpha_mask = vec![255u8; 4];
        let creative_depth = 5.0;
        
        let result = composite_segment(
            &base_frame,
            &creative_frame,
            &depth_map,
            &alpha_mask,
            width,
            height,
            creative_depth
        );
        
        // Should return base frame unchanged due to invalid input
        assert_eq!(result, base_frame);
    }

    #[test]
    fn test_edge_cases() {
        // Test zero alpha
        let result = composite_with_depth(
            &vec![255u8, 0, 0, 255], // Red base
            &vec![0u8, 255, 0, 255], // Green creative
            &vec![10.0f32],          // Creative in front
            &vec![0u8],              // Zero alpha
            1, 1,
            5.0
        );
        
        // Should remain red (base) due to zero alpha
        assert_eq!(result, vec![255u8, 0, 0, 255]);
        
        // Test full alpha
        let result = composite_with_depth(
            &vec![255u8, 0, 0, 255], // Red base
            &vec![0u8, 255, 0, 255], // Green creative
            &vec![10.0f32],          // Creative in front
            &vec![255u8],            // Full alpha
            1, 1,
            5.0
        );
        
        // Should be green (creative)
        assert_eq!(result, vec![0u8, 255, 0, 255]);
    }

    #[test]
    fn test_get_version_info() {
        let version = get_version_info();
        assert!(version.contains("Inscenium Edge Worker WASM"));
        assert!(version.contains("Rust"));
    }
}