import json
from pathlib import Path
from typing import Union, Any


class Storage:
    """Helper around a directory used for persisting JSON files."""

    def __init__(self, base_dir: Union[Path, str]):
        self.set_base_dir(base_dir)

    def set_base_dir(self, base_dir: Union[Path, str]):
        """Change the base directory where files are stored."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path(self, *parts):
        p = self.base_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_json(self, rel_path: str, data: Any):
        p = self.path(rel_path)
        p.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_json(self, rel_path: str, default=None):
        p = self.path(rel_path)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return default
        return default
