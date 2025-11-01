"""Video processing CLI using Typer."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess

try:
    import typer
    import yaml
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False
    typer = None

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from inscenium.io.video_reader import VideoReader, VideoWriter, probe_video
from inscenium.perception.detect import detect
from inscenium.tracking.byte_tracker import ByteTracker
from inscenium.uaor.score import blur_estimate, uncertainty_score, occlusion_score
from inscenium.events.sgi_writer import SGIWriter
from inscenium.render.overlay import OverlayRenderer
from inscenium.util.metrics import Metrics
from inscenium.util.logging import setup_logging
from inscenium import __version__
from inscenium.util.fs import safe_mkdirs

app = typer.Typer() if HAS_TYPER else None


def get_git_sha() -> Optional[str]:
    """Get current git SHA if available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]
    except:
        pass
    return None


def load_config(profile: str) -> dict:
    """Load pipeline configuration."""
    config_path = Path(f"configs/pipeline/{profile}_default.yaml")
    if not config_path.exists():
        # Fallback config
        return {
            "profile": profile,
            "decode": {"every_nth": 1, "max_failures": 100},
            "perception": {"detector": "torchvision_frcnn", "score_threshold": 0.5},
            "tracking": {"type": "byte", "max_age": 30, "iou_thresh": 0.3},
            "uaor": {"enable": True, "blur_kernel": 5, "conf_decay_alpha": 0.15},
            "render": {"enable": True, "trails": True, "font_scale": 0.5},
            "export": {
                "write_overlay_mp4": True,
                "write_events_jsonl": True,
                "write_tracks_jsonl": True,
                "write_metrics_json": True,
                "write_crops": False,
                "write_thumbs": True
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def generate_demo_video(output_path: Path):
    """Generate a simple demo video with moving rectangles."""
    try:
        import cv2
        import numpy as np
        
        # Video properties
        fps = 30
        duration_sec = 2
        frames = fps * duration_sec
        size = (640, 480)
        
        with VideoWriter(str(output_path), fps, size) as writer:
            for frame_idx in range(frames):
                # Create black frame
                frame = np.zeros((size[1], size[0], 3), dtype=np.uint8)
                
                # Draw moving rectangles
                t = frame_idx / frames
                
                # Red rectangle moving left to right
                x1 = int(50 + 400 * t)
                cv2.rectangle(frame, (x1, 100), (x1 + 80, 180), (0, 0, 255), -1)
                
                # Blue rectangle moving top to bottom
                y1 = int(50 + 300 * t)
                cv2.rectangle(frame, (300, y1), (380, y1 + 60), (255, 0, 0), -1)
                
                # Green circle
                center_x = int(500 - 200 * t)
                cv2.circle(frame, (center_x, 300), 40, (0, 255, 0), -1)
                
                writer.write(frame)
                
        print(f"Generated demo video: {output_path}")
        
    except Exception as e:
        print(f"Failed to generate demo video: {e}")
        raise


@app.command() if HAS_TYPER else lambda: None
def video(
    input_path: str = typer.Option(..., "--in", help="Input video path"),
    output_dir: str = typer.Option(..., "--out", help="Output directory"),
    profile: str = typer.Option("cpu", help="Pipeline profile"),
    zones: Optional[str] = typer.Option(None, help="Zones JSON file"),
    every_nth: int = typer.Option(1, help="Process every Nth frame"),
    render_overlay: str = typer.Option("yes", help="Render overlay (yes/no)"),
    max_failures: int = typer.Option(100, help="Max decode failures before stop"),
    max_frames: Optional[int] = typer.Option(None, "--max-frames", help="Max frames to process (alias for decode.max_frames)"),
    pretty: bool = typer.Option(False, "--pretty/--no-pretty", help="Enable pretty output with progress bars"),
    quiet: bool = typer.Option(False, "--quiet", help="Reduce log verbosity"),
    json_logs: bool = typer.Option(False, "--json-logs", help="Force JSON log format"),
    hud: str = typer.Option("no", help="Enable HUD overlay (yes/no)")
):
    """Process video through Inscenium pipeline."""
    
    # Set logging environment variables based on flags
    if json_logs:
        os.environ["INS_LOG_FORMAT"] = "json"
    elif pretty and HAS_RICH:
        os.environ["INS_LOG_FORMAT"] = "rich"
    else:
        os.environ.pop("INS_LOG_FORMAT", None)
    
    # Generate run ID
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    start_time = datetime.now()
    
    # Setup paths
    input_path = Path(input_path)
    output_dir = Path(output_dir) / run_id
    safe_mkdirs(str(output_dir))
    
    # Setup logging
    log_level = "WARNING" if quiet else "INFO"
    logger = setup_logging(run_id, output_dir / "logs", log_level)
    
    # Show pretty banner if enabled
    if pretty and HAS_RICH:
        console = Console()
        banner = Panel.fit(
            f"🎬 [bold blue]Inscenium[/bold blue] v{__version__}\n"
            f"Run ID: [yellow]{run_id}[/yellow]\n"
            f"Profile: [green]{profile}[/green]\n"
            f"Input: [cyan]{input_path.name}[/cyan]",
            title="Video Processing Pipeline",
            border_style="blue"
        )
        console.print(banner)
    logger.info(f"Starting video processing: {input_path}")
    
    # Generate demo video if needed
    if not input_path.exists() and str(input_path).endswith("demo.mp4"):
        logger.info("Generating demo video...")
        input_path.parent.mkdir(parents=True, exist_ok=True)
        generate_demo_video(input_path)
    
    if not input_path.exists():
        logger.error(f"Input video not found: {input_path}")
        raise typer.Exit(1)
    
    # Load configuration
    config = load_config(profile)
    logger.info(f"Loaded profile: {profile}")
    
    # Override config with CLI args
    config["decode"]["every_nth"] = every_nth
    config["decode"]["max_failures"] = max_failures
    config["render"]["enable"] = render_overlay.lower() == "yes"
    config["render"]["hud"] = hud.lower() == "yes"
    
    # Wire max_frames to decode.max_frames if provided
    if max_frames is not None:
        config.setdefault("decode", {})["max_frames"] = max_frames
    
    # Initialize pipeline components
    metrics = Metrics()
    tracker = ByteTracker(
        max_age=config["tracking"]["max_age"],
        iou_thresh=config["tracking"]["iou_thresh"]
    )
    sgi_writer = SGIWriter(output_dir)
    
    if zones:
        sgi_writer.load_zones(zones)
        
    renderer = OverlayRenderer(
        font_scale=config["render"]["font_scale"],
        trails=config["render"]["trails"],
        hud=config["render"]["hud"],
        run_id=run_id,
        profile=profile
    ) if config["render"]["enable"] else None
    
    # Probe input video
    probe_info = probe_video(str(input_path))
    logger.info(f"Video info: {probe_info}")
    
    # Setup output video writer
    video_writer = None
    if config["export"]["write_overlay_mp4"] and renderer:
        overlay_path = output_dir / "overlay.mp4"
        video_writer = VideoWriter(
            str(overlay_path), 
            probe_info.get("fps", 30), 
            (probe_info.get("width", 640), probe_info.get("height", 480))
        )
    
    try:
        # Process video
        with VideoReader(
            str(input_path), 
            every_nth=config["decode"]["every_nth"],
            max_failures=config["decode"]["max_failures"]
        ) as reader:
            
            if video_writer:
                video_writer.__enter__()
            
            frame_count = 0
            total_frames = probe_info.get("frames", 0) // config["decode"]["every_nth"]
            
            # Setup progress tracking
            progress = None
            if pretty and HAS_RICH:
                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=console
                )
                decode_task = progress.add_task("🎬 Decoding", total=total_frames)
                detect_task = progress.add_task("👁️  Detection", total=total_frames)
                track_task = progress.add_task("🏃 Tracking", total=total_frames)
                render_task = progress.add_task("🎨 Rendering", total=total_frames)
                progress.start()
            
            for frame_idx, ts_sec, frame_bgr in reader.frames():
                frame_start = time.time()
                
                try:
                    # Stage 1: Detection
                    detect_start = metrics.timer_start("detection")
                    detections = detect(
                        frame_bgr, 
                        config["perception"]["score_threshold"]
                    )
                    metrics.timer_end("detection", detect_start)
                    
                    if not detections:
                        metrics.increment("frames_no_detections")
                    
                    # Stage 2: Tracking
                    track_start = metrics.timer_start("tracking")
                    tracks = tracker.update(detections)
                    metrics.timer_end("tracking", track_start)
                    
                    # Stage 3: UAOR scoring
                    uaor_start = metrics.timer_start("uaor")
                    
                    frame_blur = blur_estimate(frame_bgr, config["uaor"]["blur_kernel"])
                    
                    # Calculate average uncertainty for all tracks
                    avg_uncertainty = 0.0
                    if tracks:
                        uncertainties = [
                            uncertainty_score(track, config["uaor"]["conf_decay_alpha"]) 
                            for track in tracks
                        ]
                        avg_uncertainty = sum(uncertainties) / len(uncertainties)
                    
                    occlusion = occlusion_score({}, tracks)
                    
                    uaor_scores = {
                        "occlusion": occlusion,
                        "uncertainty": avg_uncertainty,
                        "blur": frame_blur
                    }
                    
                    metrics.timer_end("uaor", uaor_start)
                    
                    # Stage 4: Write SGI data
                    sgi_start = metrics.timer_start("sgi_write")
                    
                    # Add track IDs to detections for SGI
                    objects_with_ids = []
                    for i, det in enumerate(detections):
                        if i < len(tracks):
                            det_with_id = det.copy()
                            det_with_id["id"] = tracks[i]["id"]
                            objects_with_ids.append(det_with_id)
                        else:
                            det_with_id = det.copy()
                            det_with_id["id"] = -1
                            objects_with_ids.append(det_with_id)
                    
                    sgi_writer.write_frame_data(
                        frame_idx, ts_sec, objects_with_ids, tracks, uaor_scores
                    )
                    metrics.timer_end("sgi_write", sgi_start)
                    
                    # Stage 5: Render overlay (optional)
                    if renderer and config["render"]["enable"]:
                        render_start = metrics.timer_start("render")
                        
                        overlay_frame = renderer.render_frame(frame_bgr, tracks, uaor_scores)
                        
                        if video_writer:
                            video_writer.write(overlay_frame)
                            
                        # Save thumbnails for interesting moments
                        if (config["export"]["write_thumbs"] and 
                            (len(tracks) > 0 or frame_idx % 30 == 0)):
                            renderer.save_thumbnail(
                                overlay_frame, frame_idx, output_dir / "thumbs"
                            )
                        
                        metrics.timer_end("render", render_start)
                    
                    # Update metrics
                    frame_time = time.time() - frame_start
                    metrics.update_fps(frame_time)
                    metrics.increment("frames_processed")
                    frame_count += 1
                    
                    # Update progress bars
                    if progress:
                        progress.update(decode_task, completed=frame_count)
                        progress.update(detect_task, completed=frame_count)
                        progress.update(track_task, completed=frame_count)
                        if config["render"]["enable"]:
                            progress.update(render_task, completed=frame_count)
                    
                    # Progress logging
                    if frame_count % 100 == 0:
                        logger.info(f"Processed {frame_count} frames, "
                                  f"FPS: {metrics.get_avg_fps():.1f}, "
                                  f"Tracks: {len(tracks)}")
                    
                except Exception as e:
                    logger.warning(f"Frame {frame_idx} processing failed: {e}")
                    metrics.increment("frames_dropped")
                    continue
            
        # Finalize
        if progress:
            progress.stop()
            
        if video_writer:
            video_writer.__exit__(None, None, None)
            
        logger.info(f"Processing complete. {frame_count} frames processed")
        
        # Write final metrics
        end_time = datetime.now()
        if config["export"]["write_metrics_json"]:
            final_metrics = metrics.to_dict()
            final_metrics.update({
                "profile": profile,
                "git_sha": get_git_sha(),
                "input_video": str(input_path),
                "run_id": run_id,
                "config": config
            })
            
            metrics_path = output_dir / "metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump(final_metrics, f, indent=2)
        
        # Write run.json metadata
        run_metadata = {
            "run_id": run_id,
            "profile": profile,
            "input_video": str(input_path),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_sec": (end_time - start_time).total_seconds(),
            "frames_processed": frame_count,
            "version": __version__,
            "git_sha": get_git_sha()
        }
        
        run_path = output_dir / "run.json"
        with open(run_path, 'w') as f:
            json.dump(run_metadata, f, indent=2)
        
        # Show pretty metrics summary
        if pretty and HAS_RICH:
            console = Console()
            
            table = Table(title="Pipeline Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Frames Processed", str(frame_count))
            table.add_row("Average FPS", f"{metrics.get_avg_fps():.2f}")
            table.add_row("Runtime", f"{run_metadata['duration_sec']:.1f}s")
            
            stage_latencies = metrics.get_stage_latencies()
            for stage, latency in stage_latencies.items():
                table.add_row(f"{stage.title()} Latency", f"{latency*1000:.1f}ms")
            
            console.print(table)
            
        logger.info(f"Results saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise typer.Exit(1)


@app.command() if HAS_TYPER else lambda: None  
def config(
    action: str = typer.Argument(help="Action: 'show' or 'list'"),
    profile: str = typer.Option("cpu", help="Profile to show (for 'show' action)")
):
    """Show configuration or list available profiles."""
    
    if action == "show":
        # Show effective configuration for profile
        config_data = load_config(profile)
        
        if HAS_RICH:
            console = Console()
            
            def print_section(title: str, data: dict, level=0):
                indent = "  " * level
                console.print(f"{indent}[bold cyan]{title}[/bold cyan]")
                for key, value in data.items():
                    if isinstance(value, dict):
                        print_section(key, value, level + 1)
                    else:
                        console.print(f"{indent}  {key}: [green]{value}[/green]")
            
            console.print(f"[bold blue]Configuration for profile: {profile}[/bold blue]")
            print_section("Settings", config_data)
        else:
            print(f"Configuration for profile: {profile}")
            print(json.dumps(config_data, indent=2))
            
    elif action == "list":
        # List available pipeline profiles
        configs_dir = Path("configs/pipeline")
        if not configs_dir.exists():
            typer.echo("No pipeline configs directory found")
            return
            
        profiles = []
        for config_file in configs_dir.glob("*_default.yaml"):
            profile_name = config_file.stem.replace("_default", "")
            profiles.append(profile_name)
            
        if HAS_RICH:
            console = Console()
            table = Table(title="Available Pipeline Profiles")
            table.add_column("Profile", style="cyan")
            table.add_column("Config File", style="green")
            
            for profile_name in sorted(profiles):
                config_file = f"{profile_name}_default.yaml"
                table.add_row(profile_name, config_file)
                
            console.print(table)
        else:
            print("Available pipeline profiles:")
            for profile_name in sorted(profiles):
                print(f"  {profile_name}")
                
    else:
        typer.echo(f"Unknown action: {action}. Use 'show' or 'list'")
        raise typer.Exit(1)


def main():
    """Main entry point."""
    if not HAS_TYPER:
        print("Error: typer not available. Install with: pip install typer pyyaml")
        return 1
        
    app()


if __name__ == "__main__":
    main()