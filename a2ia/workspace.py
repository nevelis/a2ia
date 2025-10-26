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
        target = self.resolve_path(path)
        removed = 0
        for root, dirs, files in os.walk(target, topdown=False):
            for d in dirs:
                dir_path = Path(root) / d
                if not any(dir_path.iterdir()):
                    if not dry_run:
                        dir_path.rmdir()
                    removed += 1
        return {"success": True, "path": str(target), "removed": removed, "dry_run": dry_run}

    def __repr__(self):
        return f"<Workspace path={self.path}>"