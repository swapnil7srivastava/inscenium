# Golden Scenes Test Suite

## Overview

The Golden Scenes test suite provides deterministic test data for validating the complete Inscenium pipeline. These tests ensure consistent behavior across different environments and detect regressions in processing quality.

## Test Structure

### Test Assets Directory
```
tests/golden_scenes/
├── assets/                 # Small test video clips (put tiny clips here)
│   ├── sample_001.mp4     # 5-second action scene
│   ├── sample_002.mp4     # 3-second product shot
│   └── sample_003.mp4     # 8-second interior scene
├── metadata/              # Expected results and configurations
│   ├── scenes.json        # Scene descriptions and parameters
│   ├── expected_prs.json  # Expected PRS scores for validation
│   └── expected_metrics.json # Expected processing metrics
└── README.md              # This file
```

### Usage Instructions

1. **Add Test Clips**: Place small video files (< 10MB each) in the `assets/` directory
   - Use short clips (3-10 seconds) to minimize CI time
   - Include various scene types: indoor, outdoor, product shots, action sequences
   - Ensure clips have stable surfaces suitable for placement testing

2. **Run Golden Tests**: Execute the golden scene validation
   ```bash
   make golden
   ```

3. **Update Expected Results**: When making intentional changes to algorithms
   ```bash
   make golden-update  # Updates expected results with current outputs
   ```

## Test Scenarios

### Scenario 1: Simple Interior Scene
- **File**: `sample_001.mp4`
- **Description**: Clean interior with wall surfaces
- **Expected Surfaces**: 2-3 suitable wall placements
- **Expected PRS Range**: 80-95 for primary surfaces

### Scenario 2: Product Demonstration
- **File**: `sample_002.mp4`
- **Description**: Product on table with clean background
- **Expected Surfaces**: 1-2 table surfaces, possible wall background
- **Expected PRS Range**: 85-98 for table surface

### Scenario 3: Complex Movement Scene
- **File**: `sample_003.mp4`
- **Description**: Scene with camera motion and multiple objects
- **Expected Surfaces**: 1-2 surfaces with lower stability scores
- **Expected PRS Range**: 60-80 due to motion complexity

## Deterministic Testing

### Reproducible Results
- All tests use fixed random seeds (seed=42 for numpy operations)
- Mock functions return consistent values based on input parameters
- Database operations use deterministic ordering
- Timestamp fields use fixed test dates

### Validation Criteria
- **PRS Scores**: Must be within ±2.0 points of expected values
- **Surface Count**: Must match expected counts exactly
- **Processing Time**: Must complete within performance thresholds
- **Memory Usage**: Must not exceed baseline memory consumption

## Test Data Format

### scenes.json Structure
```json
{
  "test_suite_version": "1.0.0",
  "created_at": "2024-01-15T12:00:00Z",
  "scenes": [
    {
      "scene_id": "scene_001",
      "filename": "sample_001.mp4",
      "description": "Interior wall placement test",
      "duration_seconds": 5.0,
      "resolution": [1920, 1080],
      "fps": 30,
      "test_parameters": {
        "min_prs_threshold": 70.0,
        "surface_types_expected": ["wall"],
        "complexity": "low"
      }
    }
  ]
}
```

### expected_prs.json Structure
```json
{
  "test_suite_version": "1.0.0",
  "tolerance": 2.0,
  "expectations": [
    {
      "scene_id": "scene_001",
      "expected_surfaces": [
        {
          "surface_id": "wall_primary",
          "expected_prs": 87.5,
          "prs_components": {
            "technical_score": 85.2,
            "visibility_score": 90.1,
            "temporal_score": 89.3,
            "spatial_score": 88.7,
            "brand_safety_score": 95.0
          }
        }
      ]
    }
  ]
}
```

### expected_metrics.json Structure
```json
{
  "test_suite_version": "1.0.0",
  "performance_baselines": [
    {
      "scene_id": "scene_001",
      "metrics": {
        "processing_time_ms": 1250,
        "memory_peak_mb": 245.7,
        "perception_time_ms": 450,
        "sgi_build_time_ms": 320,
        "quality_check_time_ms": 180,
        "sidecar_gen_time_ms": 95
      },
      "quality_metrics": {
        "depth_estimation_accuracy": 0.89,
        "surface_detection_precision": 0.92,
        "temporal_coherence": 0.87,
        "overall_pipeline_quality": 0.88
      }
    }
  ]
}
```

## Adding New Test Cases

### Step 1: Prepare Video Asset
1. Create or obtain a short video clip (3-10 seconds)
2. Ensure the clip has identifiable surfaces suitable for placement
3. Keep file size under 10MB for CI efficiency
4. Use standard formats (MP4 H.264) for compatibility

### Step 2: Generate Baseline
1. Place the video file in `assets/` directory
2. Run the pipeline manually to generate initial results
3. Verify the results are reasonable and expected
4. Document the expected behavior in scene metadata

### Step 3: Update Configuration
1. Add scene description to `scenes.json`
2. Add expected PRS scores to `expected_prs.json`
3. Add performance baselines to `expected_metrics.json`
4. Include detailed description of what the test validates

### Step 4: Validate Test
1. Run `make golden` to ensure the test passes
2. Run the test multiple times to verify deterministic behavior
3. Test on different environments (local, CI) to ensure portability
4. Document any special requirements or considerations

## Continuous Integration

### Automated Testing
- Golden scene tests run automatically on every PR
- Results are compared against expected values with tolerance thresholds
- Performance regressions trigger CI failures
- Memory usage is monitored for memory leaks

### Test Reporting
- Detailed test results are captured in CI artifacts
- Performance trends are tracked over time
- Quality metrics are reported in PR comments
- Failed tests include diff outputs for debugging

## Troubleshooting

### Common Issues

**Test Failures After Algorithm Changes**
- Review if changes are intentional improvements
- Update expected results if behavior is correct
- Use `make golden-update` to refresh baselines
- Ensure tolerance thresholds are appropriate

**Performance Regression Failures**
- Check for memory leaks or inefficient algorithms
- Profile the pipeline to identify bottlenecks
- Consider if performance changes are acceptable
- Update baselines if new requirements are reasonable

**Non-Deterministic Results**
- Verify all random operations use fixed seeds
- Check for system-dependent behavior
- Ensure mock functions return consistent values
- Review timestamp and ordering dependencies

### Debugging Commands
```bash
# Run single scene test with verbose output
make golden-debug SCENE=scene_001

# Compare current results with expected
make golden-diff

# Update baselines after verifying changes
make golden-update

# Run performance profiling
make golden-profile
```

## Maintenance

### Regular Tasks
- Review test coverage monthly
- Update test assets if requirements change
- Refresh performance baselines quarterly
- Validate test portability across environments

### Version Management
- Test suite version tracks breaking changes
- Backward compatibility maintained where possible
- Migration guides provided for major updates
- Historical baselines preserved for regression analysis

---

**Last Updated**: January 15, 2024  
**Test Suite Version**: 1.0.0  
**Maintainer**: Inscenium Engineering Team