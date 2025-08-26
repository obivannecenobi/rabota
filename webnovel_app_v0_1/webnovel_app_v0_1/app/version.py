from pathlib import Path

def get_version() -> str:
    vf = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return vf.read_text(encoding="utf-8").strip()
    except Exception:
        return "0.0.0"
