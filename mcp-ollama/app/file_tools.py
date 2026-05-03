import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import WORKSPACE, SUPPORTED_EXTENSIONS, MAX_FILE_CHARS, MAX_FILES_PER_REQUEST, IGNORED_FOLDERS
from app.safety import safe_path, is_ignored_path, is_binary_file, create_backup, log_edit, redact_secrets

def list_files(folder: str = ".") -> Dict[str, Any]:
    """List files and directories in a folder."""
    try:
        path = safe_path(folder)
        if not path.exists():
            return {"success": False, "error": "Folder does not exist"}

        items = []
        for item in path.iterdir():
            if is_ignored_path(item):
                continue
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })

        return {"success": True, "data": {"items": items}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_file(file_path: str) -> Dict[str, Any]:
    """Read a file's content."""
    try:
        path = safe_path(file_path)
        if not path.exists() or not path.is_file():
            return {"success": False, "error": "File does not exist"}

        if is_binary_file(path):
            return {"success": False, "error": "Binary files cannot be read"}

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS and not path.name.lower().startswith('.env'):
            return {"success": False, "error": f"Unsupported file type: {ext}"}

        content = path.read_text(encoding='utf-8', errors='ignore')
        content = content[:MAX_FILE_CHARS]  # Limit size

        # Redact secrets if needed
        content = redact_secrets(content, path)

        return {"success": True, "data": {"content": content, "truncated": len(content) == MAX_FILE_CHARS}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_files(query: str, folder: str = ".") -> Dict[str, Any]:
    """Search for files and content matching a query."""
    try:
        path = safe_path(folder)
        if not path.exists():
            return {"success": False, "error": "Folder does not exist"}

        results = []
        file_count = 0

        for root, dirs, files in os.walk(path):
            root_path = Path(root)

            # Skip ignored folders
            dirs[:] = [d for d in dirs if not is_ignored_path(root_path / d)]

            for file in files:
                if file_count >= MAX_FILES_PER_REQUEST:
                    break

                file_path = root_path / file
                if is_ignored_path(file_path):
                    continue

                try:
                    # Check filename
                    if query.lower() in file.lower():
                        results.append({
                            "file": str(file_path.relative_to(WORKSPACE)),
                            "match_type": "filename",
                            "snippet": ""
                        })
                        file_count += 1
                        continue

                    # Check content
                    if not is_binary_file(file_path):
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if query.lower() in content.lower():
                            # Find snippet
                            lines = content.split('\n')
                            snippet_lines = []
                            for i, line in enumerate(lines):
                                if query.lower() in line.lower():
                                    start = max(0, i-2)
                                    end = min(len(lines), i+3)
                                    snippet_lines = lines[start:end]
                                    break
                            snippet = '\n'.join(snippet_lines)
                            results.append({
                                "file": str(file_path.relative_to(WORKSPACE)),
                                "match_type": "content",
                                "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet
                            })
                            file_count += 1

                except:
                    continue

        return {"success": True, "data": {"results": results}}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_file(file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """Create a new file."""
    try:
        path = safe_path(file_path)
        if path.exists() and not overwrite:
            return {"success": False, "error": "File already exists. Use overwrite=true to replace."}

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

        log_edit("create", str(path.relative_to(WORKSPACE)), {"overwrite": overwrite})

        return {"success": True, "message": "File created successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_file(file_path: str, content: str) -> Dict[str, Any]:
    """Update an entire file."""
    try:
        path = safe_path(file_path)
        if not path.exists():
            return {"success": False, "error": "File does not exist"}

        if is_binary_file(path):
            return {"success": False, "error": "Cannot edit binary files"}

        # Create backup
        backup_path = create_backup(path)

        # Update file
        path.write_text(content, encoding='utf-8')

        log_edit("update", str(path.relative_to(WORKSPACE)), {"backup": str(backup_path.relative_to(WORKSPACE))})

        return {"success": True, "message": "File updated successfully", "backup": str(backup_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def patch_file(file_path: str, old_text: str, new_text: str, allow_multiple: bool = False) -> Dict[str, Any]:
    """Patch a file by replacing exact text."""
    try:
        path = safe_path(file_path)
        if not path.exists():
            return {"success": False, "error": "File does not exist"}

        if is_binary_file(path):
            return {"success": False, "error": "Cannot edit binary files"}

        content = path.read_text(encoding='utf-8', errors='ignore')

        count = content.count(old_text)
        if count == 0:
            return {"success": False, "error": "Old text not found"}
        if count > 1 and not allow_multiple:
            return {"success": False, "error": "Old text appears multiple times. Use allow_multiple=true"}

        # Create backup
        backup_path = create_backup(path)

        # Apply patch
        new_content = content.replace(old_text, new_text, 1 if not allow_multiple else -1)
        path.write_text(new_content, encoding='utf-8')

        log_edit("patch", str(path.relative_to(WORKSPACE)), {
            "backup": str(backup_path.relative_to(WORKSPACE)),
            "occurrences": count
        })

        return {"success": True, "message": "File patched successfully", "backup": str(backup_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def append_to_file(file_path: str, content: str) -> Dict[str, Any]:
    """Append content to a file."""
    try:
        path = safe_path(file_path)
        if not path.exists():
            return {"success": False, "error": "File does not exist"}

        if is_binary_file(path):
            return {"success": False, "error": "Cannot edit binary files"}

        # Create backup
        backup_path = create_backup(path)

        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)

        log_edit("append", str(path.relative_to(WORKSPACE)), {"backup": str(backup_path.relative_to(WORKSPACE))})

        return {"success": True, "message": "Content appended successfully", "backup": str(backup_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def rename_file(old_path: str, new_path: str) -> Dict[str, Any]:
    """Rename/move a file."""
    try:
        old = safe_path(old_path)
        new = safe_path(new_path)

        if not old.exists():
            return {"success": False, "error": "Source file does not exist"}

        if new.exists():
            return {"success": False, "error": "Destination already exists"}

        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)

        log_edit("rename", str(new.relative_to(WORKSPACE)), {"old_path": old_path})

        return {"success": True, "message": "File renamed successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_file(file_path: str, force: bool = False) -> Dict[str, Any]:
    """Delete a file (move to trash by default)."""
    try:
        path = safe_path(file_path)
        if not path.exists():
            return {"success": False, "error": "File does not exist"}

        if force:
            path.unlink()
            log_edit("delete_force", str(path.relative_to(WORKSPACE)))
            return {"success": True, "message": "File permanently deleted"}
        else:
            # Move to trash
            from app.config import TRASH_DIR
            trash_dir = WORKSPACE / TRASH_DIR
            trash_dir.mkdir(exist_ok=True)

            relative = path.relative_to(WORKSPACE)
            trash_path = trash_dir / relative
            trash_path.parent.mkdir(parents=True, exist_ok=True)

            import shutil
            shutil.move(str(path), str(trash_path))

            log_edit("delete_trash", str(path.relative_to(WORKSPACE)), {"trash_path": str(trash_path.relative_to(WORKSPACE))})

            return {"success": True, "message": "File moved to trash", "trash_path": str(trash_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def restore_backup(backup_path: str) -> Dict[str, Any]:
    """Restore a file from backup."""
    try:
        backup = safe_path(backup_path)
        if not backup.exists():
            return {"success": False, "error": "Backup does not exist"}

        # Find original path (remove backup directory and timestamp prefix)
        backup_parts = backup.relative_to(WORKSPACE).parts
        from app.config import BACKUP_DIR
        prefix = BACKUP_DIR.parts
        if len(backup_parts) <= len(prefix) or tuple(backup_parts[:len(prefix)]) != prefix:
            return {"success": False, "error": "Invalid backup path"}

        original_relative = Path(*backup_parts[len(prefix) + 1:])
        original_path = WORKSPACE / original_relative

        # Create backup of current file if it exists
        if original_path.exists():
            current_backup = create_backup(original_path)

        # Restore
        import shutil
        shutil.copy2(backup, original_path)

        log_edit("restore", str(original_relative), {"from_backup": backup_path})

        return {"success": True, "message": "File restored from backup"}
    except Exception as e:
        return {"success": False, "error": str(e)}