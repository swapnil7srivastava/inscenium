"""HTML report generator for pipeline runs."""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def generate_sparkline_svg(values: List[float], width: int = 100, height: int = 20) -> str:
    """Generate simple SVG sparkline from values."""
    if not values or len(values) < 2:
        return f'<svg width="{width}" height="{height}"></svg>'
    
    min_val = min(values)
    max_val = max(values)
    val_range = max_val - min_val if max_val > min_val else 1
    
    points = []
    for i, val in enumerate(values):
        x = (i / (len(values) - 1)) * width
        y = height - ((val - min_val) / val_range) * height
        points.append(f"{x:.1f},{y:.1f}")
    
    path = " ".join(points)
    
    return f'''
    <svg width="{width}" height="{height}" style="display: inline-block;">
        <polyline points="{path}" 
                  fill="none" 
                  stroke="#2563eb" 
                  stroke-width="1.5"/>
    </svg>
    '''


def load_run_data(run_dir: Path) -> Optional[Dict[str, Any]]:
    """Load run metadata and metrics."""
    run_json = run_dir / "run.json"
    metrics_json = run_dir / "metrics.json"
    
    if not run_json.exists():
        return None
        
    try:
        with open(run_json, 'r') as f:
            run_data = json.load(f)
            
        if metrics_json.exists():
            with open(metrics_json, 'r') as f:
                metrics_data = json.load(f)
            run_data["metrics"] = metrics_data
        else:
            run_data["metrics"] = {}
            
        return run_data
    except Exception:
        return None


def get_thumbnail_gallery(run_dir: Path) -> str:
    """Generate thumbnail gallery HTML."""
    thumbs_dir = run_dir / "thumbs"
    if not thumbs_dir.exists():
        return "<p>No thumbnails available</p>"
        
    thumbnails = list(thumbs_dir.glob("*.jpg"))[:12]  # Limit to 12 thumbs
    if not thumbnails:
        return "<p>No thumbnails available</p>"
        
    gallery_html = '<div class="thumbnail-gallery">'
    for thumb in sorted(thumbnails):
        rel_path = f"thumbs/{thumb.name}"
        gallery_html += f'''
        <div class="thumbnail">
            <img src="{rel_path}" alt="{thumb.stem}" loading="lazy">
            <div class="thumbnail-label">{thumb.stem}</div>
        </div>
        '''
    gallery_html += '</div>'
    
    return gallery_html


def generate_run_report_html(run_data: Dict[str, Any], run_dir: Path) -> str:
    """Generate HTML report for a single run."""
    
    # Extract key metrics
    run_id = run_data.get("run_id", "unknown")
    profile = run_data.get("profile", "unknown")
    duration = run_data.get("duration_sec", 0)
    frames = run_data.get("frames_processed", 0)
    
    metrics = run_data.get("metrics", {})
    avg_fps = metrics.get("avg_fps", 0)
    stage_latencies = metrics.get("stage_latencies", {})
    
    # Check for overlay video
    overlay_path = run_dir / "overlay.mp4"
    overlay_link = ""
    if overlay_path.exists():
        overlay_link = f'<p><a href="overlay.mp4" class="video-link">📹 View Overlay Video</a></p>'
    
    # Generate thumbnail gallery
    gallery_html = get_thumbnail_gallery(run_dir)
    
    # Generate stage latency sparklines (mock data for demo)
    stage_charts = ""
    for stage, latency in stage_latencies.items():
        # Create mock timeline for sparkline
        mock_values = [latency * (0.8 + 0.4 * (i % 3) / 3) for i in range(10)]
        sparkline = generate_sparkline_svg(mock_values)
        stage_charts += f'''
        <tr>
            <td>{stage.title()}</td>
            <td>{latency*1000:.1f}ms</td>
            <td>{sparkline}</td>
        </tr>
        '''
    
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscenium Run Report - {run_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        .header {{
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        .header h1 {{ margin: 0 0 0.5rem 0; font-size: 2.5rem; }}
        .header p {{ margin: 0; opacity: 0.9; font-size: 1.1rem; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 0.5rem;
        }}
        .metric-label {{
            color: #64748b;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .section {{
            background: white;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .section-header {{
            background: #f1f5f9;
            padding: 1rem 1.5rem;
            font-weight: 600;
            color: #334155;
            border-bottom: 1px solid #e2e8f0;
        }}
        .section-content {{
            padding: 1.5rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
        }}
        
        .video-link {{
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 0.75rem 1.5rem;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        .video-link:hover {{
            background: #2563eb;
        }}
        
        .thumbnail-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 1rem;
        }}
        .thumbnail {{
            text-align: center;
        }}
        .thumbnail img {{
            width: 100%;
            height: 100px;
            object-fit: cover;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .thumbnail-label {{
            margin-top: 0.5rem;
            font-size: 0.8rem;
            color: #64748b;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #64748b;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Inscenium Pipeline Report</h1>
        <p>Run ID: {run_id} | Profile: {profile}</p>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{frames:,}</div>
            <div class="metric-label">Frames Processed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_fps:.1f}</div>
            <div class="metric-label">Avg FPS</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{duration:.1f}s</div>
            <div class="metric-label">Duration</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{profile}</div>
            <div class="metric-label">Profile</div>
        </div>
    </div>
    
    {overlay_link}
    
    <div class="section">
        <div class="section-header">Stage Latencies</div>
        <div class="section-content">
            <table>
                <thead>
                    <tr>
                        <th>Stage</th>
                        <th>Avg Latency</th>
                        <th>Timeline</th>
                    </tr>
                </thead>
                <tbody>
                    {stage_charts}
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="section">
        <div class="section-header">Thumbnail Gallery</div>
        <div class="section-content">
            {gallery_html}
        </div>
    </div>
    
    <div class="footer">
        Generated by Inscenium v1.0.0 at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
</body>
</html>
    '''
    
    return html_content


def generate_index_html(runs_data: List[Dict[str, Any]], runs_dir: Path) -> str:
    """Generate index.html with links to all run reports."""
    
    runs_table = ""
    for run_data in sorted(runs_data, key=lambda x: x.get("start_time", ""), reverse=True):
        run_id = run_data.get("run_id", "unknown")
        profile = run_data.get("profile", "unknown")
        frames = run_data.get("frames_processed", 0)
        duration = run_data.get("duration_sec", 0)
        start_time = run_data.get("start_time", "")
        
        # Format start time
        try:
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
        except:
            formatted_time = start_time[:16] if start_time else "Unknown"
        
        # Check for files
        run_dir = runs_dir / run_id
        has_report = (run_dir / "report.html").exists()
        has_video = (run_dir / "overlay.mp4").exists()
        
        report_link = f'<a href="{run_id}/report.html">📊 Report</a>' if has_report else "No report"
        video_link = f'<a href="{run_id}/overlay.mp4">🎥 Video</a>' if has_video else "No video"
        
        runs_table += f'''
        <tr>
            <td><strong>{run_id}</strong></td>
            <td>{formatted_time}</td>
            <td>{profile}</td>
            <td>{frames:,}</td>
            <td>{duration:.1f}s</td>
            <td>{report_link}</td>
            <td>{video_link}</td>
        </tr>
        '''
    
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscenium Runs Gallery</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8fafc;
            color: #1e293b;
        }}
        .header {{
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5rem; }}
        
        .section {{
            background: white;
            margin-bottom: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .section-header {{
            background: #f1f5f9;
            padding: 1rem 1.5rem;
            font-weight: 600;
            color: #334155;
            border-bottom: 1px solid #e2e8f0;
        }}
        .section-content {{
            padding: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #374151;
            position: sticky;
            top: 0;
        }}
        
        a {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
        }}
        a:hover {{
            color: #2563eb;
            text-decoration: underline;
        }}
        
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #64748b;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Inscenium Runs Gallery</h1>
    </div>
    
    <div class="section">
        <div class="section-header">Pipeline Runs</div>
        <div class="section-content">
            <table>
                <thead>
                    <tr>
                        <th>Run ID</th>
                        <th>Date/Time</th>
                        <th>Profile</th>
                        <th>Frames</th>
                        <th>Duration</th>
                        <th>Report</th>
                        <th>Video</th>
                    </tr>
                </thead>
                <tbody>
                    {runs_table}
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="footer">
        Generated by Inscenium v1.0.0 at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    </div>
</body>
</html>
    '''
    
    return html_content


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate HTML reports for Inscenium runs")
    parser.add_argument("--runs-dir", type=str, default="runs", help="Directory containing run folders")
    parser.add_argument("--index", action="store_true", help="Generate index.html gallery")
    
    args = parser.parse_args()
    
    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        print(f"Runs directory not found: {runs_dir}")
        return 1
        
    if args.index:
        # Generate index gallery
        print("Generating runs gallery...")
        
        all_runs = []
        for run_subdir in runs_dir.iterdir():
            if run_subdir.is_dir() and not run_subdir.name.startswith('.'):
                run_data = load_run_data(run_subdir)
                if run_data:
                    all_runs.append(run_data)
                    
        index_html = generate_index_html(all_runs, runs_dir)
        index_path = runs_dir / "index.html"
        
        with open(index_path, 'w') as f:
            f.write(index_html)
            
        print(f"Gallery saved to: {index_path}")
        
    else:
        # Generate report for latest run
        run_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if not run_dirs:
            print("No run directories found")
            return 1
            
        # Get most recent run directory
        latest_run = max(run_dirs, key=lambda x: x.stat().st_mtime)
        
        print(f"Generating report for latest run: {latest_run.name}")
        
        run_data = load_run_data(latest_run)
        if not run_data:
            print(f"Could not load run data from {latest_run}")
            return 1
            
        report_html = generate_run_report_html(run_data, latest_run)
        report_path = latest_run / "report.html"
        
        with open(report_path, 'w') as f:
            f.write(report_html)
            
        print(f"Report saved to: {report_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())