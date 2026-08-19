import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SOPS_DIR = DATA_DIR / "sops"


def _safe_read_json(path: Path) -> Any:
    """
    Safely read JSON files without crashing the app.
    - Returns {} for equipment_history.json if missing/invalid
    - Returns [] for other JSON files if missing/invalid
    """
    default_value = {} if path.name == "equipment_history.json" else []

    if not path.exists():
        print(f"DEBUG: File not found: {path}")
        return default_value

    try:
        if path.stat().st_size == 0:
            print(f"DEBUG: File is empty: {path}")
            return default_value
    except Exception as e:
        print(f"DEBUG: Could not read file size for {path}: {e}")
        return default_value

    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"DEBUG: Invalid JSON in {path}: {e}")
        return default_value
    except Exception as e:
        print(f"DEBUG: Error reading {path}: {e}")
        return default_value


def search_sops(query: str) -> list[dict[str, Any]]:
    """
    Simple keyword-based retrieval over local SOP text files.
    Keeps the MVP stable and easy to demo.
    """
    results: list[dict[str, Any]] = []
    query_terms = [term.strip().lower() for term in query.split() if term.strip()]

    if not SOPS_DIR.exists():
        print(f"DEBUG: SOPs directory not found: {SOPS_DIR}")
        return results

    for file_path in SOPS_DIR.glob("*.txt"):
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"DEBUG: Could not read SOP file {file_path}: {e}")
            continue

        lowered = content.lower()
        score = sum(1 for term in query_terms if term in lowered)

        if score > 0:
            results.append(
                {
                    "source": file_path.name,
                    "content": content[:1000],
                    "score": score,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]


def search_maintenance_logs(query: str, asset_id: str) -> list[dict[str, Any]]:
    """
    Search local maintenance logs for the selected asset.
    """
    logs_path = DATA_DIR / "maintenance_logs.json"
    print(f"DEBUG: Reading maintenance logs from: {logs_path}")

    logs = _safe_read_json(logs_path)

    if not isinstance(logs, list):
        print("DEBUG: maintenance_logs.json is not a list")
        return []

    query_terms = [term.strip().lower() for term in query.split() if term.strip()]
    results: list[dict[str, Any]] = []

    for log in logs:
        if not isinstance(log, dict):
            continue

        log_asset = str(log.get("asset_id", "")).lower()
        if log_asset != asset_id.lower():
            continue

        combined_text = " ".join(
            [
                str(log.get("issue", "")),
                str(log.get("action_taken", "")),
                str(log.get("outcome", "")),
            ]
        ).lower()

        score = sum(1 for term in query_terms if term in combined_text)

        if score > 0:
            results.append(
                {
                    "source": f"maintenance log {log.get('date', 'unknown')}",
                    "content": (
                        f"Issue: {log.get('issue', '')}. "
                        f"Action: {log.get('action_taken', '')}. "
                        f"Outcome: {log.get('outcome', '')}"
                    ),
                    "score": score,
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]


def get_equipment_history(asset_id: str) -> dict[str, Any]:
    """
    Fetch simple local equipment history.
    """
    history_path = DATA_DIR / "equipment_history.json"
    print(f"DEBUG: Reading equipment history from: {history_path}")

    history = _safe_read_json(history_path)

    if not isinstance(history, dict):
        print("DEBUG: equipment_history.json is not a dictionary")
        return {}

    asset_history = history.get(asset_id, {})
    return asset_history if isinstance(asset_history, dict) else {}