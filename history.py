import os
import json
import uuid
from datetime import datetime
from shutil import move
from helpers import ensure_dir, make_unique

HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")


def _load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history_list):
    ensure_dir(HISTORY_DIR)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, indent=2, ensure_ascii=False)


def start_transaction(target_dir, deep=False, mode="clean"):
    """
    Start and persist a new transaction record for this run.
    Returns the unique run_id.
    """
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + uuid.uuid4().hex[:6]
    record = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "target_dir": target_dir,
        "deep": deep,
        "mode": mode,
        "total_files": 0,
        "categories": {},
        "moves": [],
        "removed_dirs": [],
        "undone": False,
        "undone_at": None,
    }
    history = _load_history()
    history.insert(0, record)
    _save_history(history)
    return run_id


def record_move(run_id, src_path, dest_path):
    """Append a moved file to the transaction."""
    history = _load_history()
    for item in history:
        if item.get("run_id") == run_id:
            item.setdefault("moves", []).append({
                "src": src_path,
                "dest": dest_path,
                "time": datetime.now().isoformat()
            })
            item["total_files"] = len(item["moves"])
            _save_history(history)
            break


def record_removed_dir(run_id, dirpath):
    """Append a removed empty folder to the transaction."""
    history = _load_history()
    for item in history:
        if item.get("run_id") == run_id:
            item.setdefault("removed_dirs", []).append(dirpath)
            _save_history(history)
            break


def finish_transaction(run_id, counts=None):
    """Finalize counts and status for the transaction."""
    history = _load_history()
    for item in history:
        if item.get("run_id") == run_id:
            if counts:
                item["categories"] = counts
                item["total_files"] = sum(counts.values())
            _save_history(history)
            return item
    return None


def get_all_history():
    """Return all past transactions ordered latest first."""
    return _load_history()


def get_transaction(run_id):
    """Retrieve a single transaction by ID."""
    history = _load_history()
    for item in history:
        if item.get("run_id") == run_id:
            return item
    return None


def undo_run(run_id):
    """
    Reverse the moves recorded in a transaction.
    Moves each file from 'dest' back to 'src'.
    Returns a summary dict {success: bool, restored: int, errors: list}.
    """
    history = _load_history()
    target_item = None
    for item in history:
        if item.get("run_id") == run_id:
            target_item = item
            break

    if not target_item:
        return {"success": False, "message": "Run ID " + str(run_id) + " not found.", "restored": 0, "errors": []}

    if target_item.get("undone"):
        return {"success": False, "message": "Run ID " + str(run_id) + " was already undone.", "restored": 0, "errors": []}

    moves_list = target_item.get("moves", [])
    restored = 0
    errors = []

    for m in reversed(moves_list):
        src = m["src"]
        dest = m["dest"]

        if not os.path.exists(dest):
            errors.append("File at destination no longer exists: " + dest)
            continue

        try:
            parent_dir = os.path.dirname(src)
            ensure_dir(parent_dir)
            
            final_src = src
            if os.path.exists(src) and os.path.abspath(src) != os.path.abspath(dest):
                final_src = os.path.join(parent_dir, make_unique(parent_dir, os.path.basename(src)))

            move(dest, final_src)
            restored += 1
        except Exception as e:
            errors.append("Failed to restore " + dest + " -> " + src + ": " + str(e))

    target_item["undone"] = True
    target_item["undone_at"] = datetime.now().isoformat()
    _save_history(history)

    return {
        "success": len(errors) == 0,
        "restored": restored,
        "total_attempted": len(moves_list),
        "errors": errors,
        "message": "Restored " + str(restored) + "/" + str(len(moves_list)) + " files successfully."
    }

