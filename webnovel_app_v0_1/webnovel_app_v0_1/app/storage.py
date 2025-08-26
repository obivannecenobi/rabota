import json
from pathlib import Path

class Storage:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path(self, *parts):
        p = self.base_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_json(self, rel_path: str, data: dict):
        p = self.path(rel_path)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_json(self, rel_path: str, default=None):
        p = self.path(rel_path)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return default
        return default
