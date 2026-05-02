import os
from pathlib import Path
from typing import Optional

# Configuration settings
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
WORKSPACE: Path = Path(os.getenv("WORKSPACE", "/workspace")).resolve()

# Efficiency limits
MAX_FILE_CHARS: int = int(os.getenv("MAX_FILE_CHARS", "8000"))
MAX_TOTAL_CONTEXT_CHARS: int = int(os.getenv("MAX_TOTAL_CONTEXT_CHARS", "32000"))
MAX_FILES_PER_REQUEST: int = int(os.getenv("MAX_FILES_PER_REQUEST", "20"))

# Ignored folders
IGNORED_FOLDERS: set = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".backups",
    ".agent_logs",
}

# Supported file extensions for reading
SUPPORTED_EXTENSIONS: set = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
    ".md", ".txt", ".html", ".css", ".env.example", ".dockerfile", "Dockerfile"
}

# Dangerous paths to block
DANGEROUS_PATHS: list = [
    "..", "~", "/etc", "/root", "/var/run/docker.sock"
]