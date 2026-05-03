import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
from app.config import WORKSPACE, DANGEROUS_PATHS, IGNORED_FOLDERS, BACKUP_DIR, LOG_DIR

def safe_path(relative_path: str) -> Path:
    """Convert relative path to absolute, ensuring it stays within WORKSPACE."""
    path = (WORKSPACE / relative_path).resolve()

    if not str(path).startswith(str(WORKSPACE)):
        raise ValueError("Access denied: path outside workspace")

    # Check for dangerous patterns
    path_str = str(path)
    for dangerous in DANGEROUS_PATHS:
        if dangerous in path_str:
            raise ValueError(f"Access denied: dangerous path component '{dangerous}'")

    # Check for absolute Windows paths (basic check)
    if path_str.startswith(("C:", "D:", "E:")):
        raise ValueError("Access denied: absolute Windows path")

    return path

def is_ignored_path(path: Path) -> bool:
    """Check if path should be ignored."""
    parts = path.relative_to(WORKSPACE).parts
    return any(part in IGNORED_FOLDERS for part in parts)

def is_binary_file(path: Path) -> bool:
    """Check if file is likely binary."""
    try:
        with open(path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True
        return False
    except:
        return True

def create_backup(file_path: Path) -> Path:
    """Create a backup of the file."""
    backup_dir = WORKSPACE / BACKUP_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    relative_path = file_path.relative_to(WORKSPACE)
    backup_path = backup_dir / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(file_path, backup_path)

    return backup_path

def log_edit(operation: str, file_path: str, details: dict = None):
    """Log an edit operation."""
    log_dir = WORKSPACE / LOG_DIR
    log_dir.mkdir(exist_ok=True)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "file_path": file_path,
        "details": details or {}
    }

    log_file = log_dir / "edits.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

def redact_secrets(content: str, file_path: Path) -> str:
    """Redact potential secrets in content."""
    if file_path.name.startswith('.env'):
        # Simple redaction for .env files
        lines = content.split('\n')
        redacted = []
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                redacted.append(f"{key}=[REDACTED]")
            else:
                redacted.append(line)
        return '\n'.join(redacted)
    return content