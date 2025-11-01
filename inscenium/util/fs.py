"""File system utilities."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict


def safe_mkdirs(path: str) -> Path:
    """Safely create directory structure."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def atomic_append_jsonl(path: Path, obj: Dict[str, Any]):
    """Atomically append JSON object as line to file."""
    path = Path(path)
    
    # Create parent directories
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file first
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, 
                                   prefix=f".{path.name}.", 
                                   delete=False) as f:
        temp_path = Path(f.name)
        
        # If target exists, copy existing content
        if path.exists():
            with open(path, 'r') as existing:
                f.write(existing.read())
                
        # Append new line
        f.write(json.dumps(obj) + '\n')
        
    # Atomic rename
    temp_path.replace(path)