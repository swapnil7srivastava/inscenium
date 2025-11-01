"""Logging utilities with Rich console output."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich import traceback
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class EmojiFormatter(logging.Formatter):
    """Formatter that adds emojis for rich mode."""
    
    EMOJI_MAP = {
        "INFO": "▶️",
        "WARNING": "⚠️",
        "ERROR": "❌",  
        "DEBUG": "🐛",
        "CRITICAL": "💥"
    }
    
    def format(self, record):
        # Add emoji prefix for rich mode
        log_format = os.environ.get("INS_LOG_FORMAT", "").lower()
        if log_format == "rich" and record.levelname in self.EMOJI_MAP:
            record.msg = f"{self.EMOJI_MAP[record.levelname]} {record.msg}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if hasattr(record, 'run_id'):
            log_entry["run_id"] = record.run_id
        return json.dumps(log_entry)


def setup_logging(run_id: Optional[str] = None, 
                 log_dir: Optional[Path] = None,
                 level: str = "INFO") -> logging.Logger:
    """Set up Rich console logging with optional file output."""
    
    # Install rich traceback handler if available
    if HAS_RICH:
        traceback.install()
    
    # Get log format from environment
    log_format = os.environ.get("INS_LOG_FORMAT", "").lower()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler based on format preference
    if log_format == "json":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
    elif log_format == "rich" and HAS_RICH:
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
        # Add emoji formatter for rich mode
        console_handler.setFormatter(EmojiFormatter())
    elif HAS_RICH:
        # Default rich mode without emojis
        console = Console()
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True
        )
    else:
        # Plain console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # File handler if log directory specified
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "inscenium.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        root_logger.addHandler(file_handler)
    
    # Create inscenium logger with run_id prefix
    inscenium_logger = logging.getLogger("inscenium")
    
    if run_id:
        # Add run_id to all inscenium log messages
        class RunIdFilter:
            def __init__(self, run_id):
                self.run_id = run_id
                
            def filter(self, record):
                record.msg = f"[{self.run_id}] {record.msg}"
                return True
                
        run_filter = RunIdFilter(run_id)
        inscenium_logger.addFilter(run_filter)
    
    return inscenium_logger