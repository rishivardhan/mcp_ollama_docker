import configparser
import os
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.ini"

config = configparser.ConfigParser()
config.read(CONFIG_FILE)


def _get(section: str, key: str, fallback: str) -> str:
    env_value = os.getenv(key.upper())
    if env_value is not None:
        return env_value
    if config.has_option(section, key):
        return config.get(section, key)
    return fallback


def _comma_list(section: str, key: str, fallback: str) -> List[str]:
    raw = _get(section, key, fallback)
    return [item.strip() for item in raw.split(",") if item.strip()]


# Workspace and path settings
OLLAMA_HOST: str = _get("ollama", "host", "http://ollama:11434")
OLLAMA_MODEL: str = _get("ollama", "model", "qwen2.5-coder:3b")
WORKSPACE: Path = Path(_get("workspace", "root", "/workspace")).resolve()
BACKUP_DIR: Path = Path(_get("workspace", "backup_dir", ".backups"))
TRASH_DIR: Path = Path(_get("workspace", "trash_dir", ".trash"))
LOG_DIR: Path = Path(_get("workspace", "log_dir", ".agent_logs"))

# Efficiency limits
MAX_FILE_CHARS: int = int(_get("limits", "max_file_chars", "8000"))
MAX_TOTAL_CONTEXT_CHARS: int = int(_get("limits", "max_total_context_chars", "32000"))
MAX_FILES_PER_REQUEST: int = int(_get("limits", "max_files_per_request", "20"))

# Ignored folders
IGNORED_FOLDERS = set(_comma_list(
    "workspace",
    "ignore_folders",
    ".git,node_modules,__pycache__,.venv,venv,dist,build,.backups,.agent_logs"
))

# Supported file extensions for reading
SUPPORTED_EXTENSIONS = set(_comma_list(
    "workspace",
    "supported_extensions",
    ".py,.js,.ts,.tsx,.jsx,.json,.yaml,.yml,.md,.txt,.html,.css,.env.example,.dockerfile,Dockerfile"
))

# Default file discovery settings
DEFAULT_TARGET_FILES = _comma_list(
    "workspace",
    "default_target_files",
    ""
)
CONFIG_FILE_PATTERNS = _comma_list(
    "workspace",
    "config_file_patterns",
    ""
)

# Dangerous paths to block
DANGEROUS_PATHS = [
    "..", "~", "/etc", "/root", "/var/run/docker.sock"
]
