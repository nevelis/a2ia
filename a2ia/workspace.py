import os
import re
import time
from pathlib import Path

class Workspace:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.workspace_id = os.path.basename(self.path)
        self.description = ""
        self.created_at = time.time()

    @classmethod
    def attach(cls, path: str | Path, **_):
        return cls(path)

    def resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.path / p

    def list_directory(self, path: str = "", recursive: bool = False):
        target = self.resolve_path(path)
        if recursive:
            files = [str(p) for p in target.rglob("*") if p.is_file()]
        else:
            files = [str(p) for p in target.glob("*") if p.is_file()]
        return {"success": True, "files": files}

    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        file_path = self.resolve_path(path)
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> None:
        file_path = self.resolve_path(path)
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

    def append_file(self, path: str, content: str, encoding: str = "utf-8") -> dict:
        file_path = self.resolve_path(path)
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "a", encoding=encoding) as f:
            f.write(content)
        return {"success": True, "path": str(file_path)}

    def truncate_file(self, path: str, length: int = 0) -> dict:
        file_path = self.resolve_path(path)
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "r+b" if file_path.exists() else "wb") as f:
            f.truncate(length)
        return {"success": True, "path": str(file_path), "length": length}

    def find_replace(self, path: str, find_text: str, replace_text: str, encoding: str = "utf-8") -> dict:
        file_path = self.resolve_path(path)
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        new_content = content.replace(find_text, replace_text)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(new_content)
        return {"success": True, "path": str(file_path), "count": content.count(find_text)}

    def find_replace_regex(self, path: str, pattern: str, replace_text: str, encoding: str = "utf-8") -> dict:
        file_path = self.resolve_path(path)
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
        new_content, count = re.subn(pattern, replace_text, content)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(new_content)
        return {"success": True, "path": str(file_path), "count": count}

    def prune_directory(self, path: str, keep_patterns=None, dry_run: bool = False) -> dict:
        """Remove files not matching keep_patterns, then remove empty directories."""
        import fnmatch
        target = self.resolve_path(path)
        removed = 0
        files_removed = []
        
        if keep_patterns is None:
            keep_patterns = []
        
        # First pass: remove files that don't match keep patterns
        for root, dirs, files in os.walk(target, topdown=True):
            for f in files:
                file_path = Path(root) / f
                relative_path = file_path.relative_to(target)
                
                # Check if file matches any keep pattern
                should_keep = False
                for pattern in keep_patterns:
                    if fnmatch.fnmatch(str(relative_path), pattern) or fnmatch.fnmatch(f, pattern):
                        should_keep = True
                        break
                
                if not should_keep:
                    if not dry_run:
                        file_path.unlink()
                    files_removed.append(str(relative_path))
                    removed += 1
        
        # Second pass: remove empty directories
        for root, dirs, files in os.walk(target, topdown=False):
            for d in dirs:
                dir_path = Path(root) / d
                try:
                    if not any(dir_path.iterdir()):
                        if not dry_run:
                            dir_path.rmdir()
                        removed += 1
                except:
                    pass
        
        return {
            "success": True, 
            "path": str(target), 
            "count": removed, 
            "removed": removed, 
            "files": files_removed,
            "dry_run": dry_run
        }

    def delete_file(self, path: str, recursive: bool = False) -> dict:
        """Delete a file or directory."""
        import shutil
        file_path = self.resolve_path(path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if file_path.is_dir():
            if recursive:
                shutil.rmtree(file_path)
            else:
                file_path.rmdir()
        else:
            file_path.unlink()
        
        return {"success": True, "path": str(path)}

    def move_file(self, source: str, destination: str) -> dict:
        """Move or rename a file or directory."""
        import shutil
        src_path = self.resolve_path(source)
        dest_path = self.resolve_path(destination)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {source}")
        
        # Create parent directory of destination if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(src_path), str(dest_path))
        
        return {"success": True, "from": source, "to": destination}

    def __repr__(self):
        return f"<Workspace path={self.path}>"