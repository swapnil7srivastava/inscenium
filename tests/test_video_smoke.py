"""Smoke test for video processing pipeline."""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest


def generate_test_video(output_path: Path):
    """Generate a minimal test video."""
    try:
        import cv2
        import numpy as np
        
        # Video properties
        fps = 10
        frames = 20  # 2 seconds
        size = (320, 240)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, size)
        
        if not writer.isOpened():
            raise RuntimeError("Cannot create test video")
        
        for frame_idx in range(frames):
            # Create simple moving pattern
            frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
            
            # Moving rectangle
            x = int(10 + (200 * frame_idx / frames))
            cv2.rectangle(frame, (x, 50), (x + 50, 100), (0, 255, 0), -1)
            
            # Static circle
            cv2.circle(frame, (160, 120), 30, (255, 0, 0), -1)
            
            writer.write(frame)
            
        writer.release()
        
    except ImportError:
        # Fallback: create empty file
        output_path.touch()
        

def test_video_pipeline_smoke():
    """Test that video pipeline runs end-to-end without crashing."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Generate test video
        test_video = temp_path / "test.mp4"
        generate_test_video(test_video)
        
        if not test_video.exists():
            pytest.skip("Cannot generate test video (opencv not available)")
            
        # Run CLI
        output_dir = temp_path / "output"
        
        cmd = [
            "python", "-m", "inscenium.cli.video",
            "video",
            "--in", str(test_video),
            "--out", str(output_dir),
            "--profile", "cpu",
            "--render", "yes",
            "--every-nth", "2"
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=Path.cwd()
            )
            
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
            # Should not crash
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            
            # Check output directory was created
            run_dirs = list(output_dir.glob("*"))
            assert len(run_dirs) >= 1, "No run directory created"
            
            run_dir = run_dirs[0]
            
            # Check required files exist
            expected_files = [
                "events.sgi.jsonl",
                "tracks.jsonl", 
                "metrics.json"
            ]
            
            for filename in expected_files:
                file_path = run_dir / filename
                assert file_path.exists(), f"Missing output file: {filename}"
                
                # Check file has content
                assert file_path.stat().st_size > 0, f"Empty output file: {filename}"
            
            # Check JSONL files have valid JSON lines
            with open(run_dir / "events.sgi.jsonl", 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1, "No SGI events written"
                
                # Verify first line is valid JSON with required keys
                first_event = json.loads(lines[0])
                assert "ts" in first_event
                assert "frame" in first_event
                assert "objects" in first_event
                assert "events" in first_event
                assert "uaor" in first_event
            
            with open(run_dir / "tracks.jsonl", 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 1, "No track data written"
                
                # Verify first line is valid JSON
                first_track = json.loads(lines[0])
                assert "ts" in first_track
                assert "frame" in first_track
                assert "track" in first_track
            
            # Check metrics file
            with open(run_dir / "metrics.json", 'r') as f:
                metrics = json.load(f)
                assert "runtime_sec" in metrics
                assert "total_frames" in metrics
                assert metrics["total_frames"] > 0
                
        except subprocess.TimeoutExpired:
            pytest.fail("CLI command timed out")
        except FileNotFoundError:
            pytest.skip("inscenium CLI not available (not installed)")


def test_demo_video_generation():
    """Test demo video generation."""
    
    # Ensure samples directory exists
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)
    
    demo_path = samples_dir / "demo.mp4"
    
    # Remove existing demo if present
    if demo_path.exists():
        demo_path.unlink()
    
    # Generate demo video
    generate_test_video(demo_path)
    
    assert demo_path.exists(), "Demo video was not created"
    
    if demo_path.stat().st_size > 0:
        # Try to probe the video if opencv available
        try:
            from inscenium.io.video_reader import probe_video
            info = probe_video(str(demo_path))
            assert "fps" in info or "error" not in info
        except ImportError:
            pass  # opencv not available, skip probe test


if __name__ == "__main__":
    # Run smoke test directly
    test_video_pipeline_smoke()
    test_demo_video_generation()
    print("✓ All smoke tests passed!")