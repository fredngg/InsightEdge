import json
import os
from datetime import datetime

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")


def _folder(role: str) -> str:
    subfolder = "ent" if "Territory" in role else "velocity"
    return os.path.join(_DATA_DIR, subfolder)


def save_run(results: list, role: str, source_filename: str) -> str:
    folder = _folder(role)
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = source_filename.replace(" ", "_").replace("/", "_")
    path = os.path.join(folder, f"{timestamp}_{safe_name}.json")
    payload = {
        "metadata": {
            "source_filename": source_filename,
            "role": role,
            "date": datetime.now().isoformat(),
            "company_count": len(results),
        },
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def delete_run(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)


def load_run(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_runs(role: str) -> list[dict]:
    folder = _folder(role)
    if not os.path.exists(folder):
        return []
    runs = []
    for filename in os.listdir(folder):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(folder, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("metadata", {})
            raw_date = meta.get("date", "")
            display_date = raw_date[:16].replace("T", " ") if raw_date else "—"
            runs.append({
                "path": path,
                "source_filename": meta.get("source_filename", filename),
                "date": raw_date,
                "display_date": display_date,
                "company_count": meta.get("company_count", 0),
                "role": meta.get("role", ""),
            })
        except Exception:
            pass
    return sorted(runs, key=lambda x: x["date"], reverse=True)
