import os
import uuid
from datetime import datetime
from shutil import move

from . import config
from . import helpers
from .helpers import ensure_dir, make_unique
from .logger import LOG_DIR, start_log, write_log

HISTORY_DIR = LOG_DIR


def get_log_path(run_id: str) -> str:
    """Find the path to the log file corresponding to a run_id."""
    if not run_id:
        return ""

    safe_run_id = os.path.basename(run_id)
    candidates = [
        os.path.join(LOG_DIR, safe_run_id if safe_run_id.endswith(".log") else (safe_run_id + ".log")),
        os.path.join(LOG_DIR, (safe_run_id + ".log") if safe_run_id.startswith("run_") else ("run_" + safe_run_id + ".log")),
    ]

    for p in candidates:
        if os.path.isfile(p):
            return p

    # If not found directly by filename, search log headers in LOG_DIR
    if os.path.isdir(LOG_DIR):
        for fname in os.listdir(LOG_DIR):
            if fname.endswith(".log"):
                candidate_path = os.path.join(LOG_DIR, fname)
                try:
                    with open(candidate_path, "r", encoding="utf-8", errors="replace") as f:
                        for _ in range(10):
                            line = f.readline()
                            if not line:
                                break
                            if line.startswith("Run ID:") and safe_run_id in line:
                                return candidate_path
                except OSError:
                    continue

    # Default fallback path
    return candidates[0]


def start_transaction(target_dir="", deep=False, mode="clean", log_path=None) -> str:
    """
    Start and persist a new transaction record as its own individual log file.
    Returns the unique run_id.
    """
    if not log_path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = "run_" + timestamp + "_" + str(uuid.uuid4().hex[:6])
        start_log(target_dir=target_dir, deep=deep, mode=mode, run_id=run_id)
        return run_id

    # If an existing log_path was passed
    base = os.path.basename(log_path)
    run_id = os.path.splitext(base)[0]
    return run_id


def record_move(run_id: str, src_path: str, dest_path: str, log_path: str = None):
    """Append a moved file to the run's individual log file."""
    path = log_path or get_log_path(run_id)
    if not path or not os.path.exists(path):
        return

    entry = "MOVED: " + str(src_path) + " -> " + str(dest_path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if entry not in content:
            write_log(path, entry)
    except OSError:
        write_log(path, entry)


def record_removed_dir(run_id: str, dirpath: str, log_path: str = None):
    """Append a removed empty folder to the run's log file."""
    path = log_path or get_log_path(run_id)
    if not path or not os.path.exists(path):
        return

    entry = "REMOVED EMPTY FOLDER: " + str(dirpath)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if entry not in content:
            write_log(path, entry)
    except OSError:
        write_log(path, entry)


def finish_transaction(run_id: str, counts: dict = None, log_path: str = None):
    """Finalize summary and category metrics inside the run's log file."""
    path = log_path or get_log_path(run_id)
    if not path or not os.path.exists(path):
        return None

    if counts:
        total = sum(counts.values())
        summary_lines = [
            "",
            "--- SUMMARY ---",
            "Total files moved: " + str(total)
        ]
        for cat, cnt in counts.items():
            if cnt > 0:
                summary_lines.append(str(cat) + ": " + str(cnt))
        summary_lines.append("Run completed: " + str(datetime.now().isoformat()) + "\n")
        write_log(path, "\n".join(summary_lines))

    return get_transaction(run_id)


def parse_log_file(filepath: str) -> dict:
    """Parse a single run .log file into a structured transaction dict."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return None

    filename = os.path.basename(filepath)
    run_id = os.path.splitext(filename)[0]

    timestamp = None
    target_dir = ""
    deep = False
    mode = "clean"
    undone = False
    undone_at = None
    moves = []
    removed_dirs = []
    categories = {cat: 0 for cat in config.CATEGORY_ORDER}

    for line in content.splitlines():
        line_str = line.strip()
        if line_str.startswith("Run ID:"):
            run_id = line_str.split("Run ID:", 1)[1].strip()
        elif line_str.startswith("Run started:"):
            timestamp = line_str.split("Run started:", 1)[1].strip()
        elif line_str.startswith("Target:"):
            target_val = line_str.split("Target:", 1)[1].strip()
            if "(deep scan)" in target_val.lower():
                deep = True
                target_dir = target_val.replace("(deep scan)", "").replace("(Deep Scan)", "").strip()
            else:
                target_dir = target_val
        elif line_str.startswith("Deep Scan:"):
            deep = line_str.split("Deep Scan:", 1)[1].strip().lower() in ("true", "1", "yes")
        elif line_str.startswith("Mode:"):
            mode = line_str.split("Mode:", 1)[1].strip()
        elif line_str.startswith("MOVED:"):
            move_str = line_str.split("MOVED:", 1)[1].strip()
            if "->" in move_str:
                src, dest = move_str.split("->", 1)
                src = src.strip()
                dest = dest.strip()
                moves.append({"src": src, "dest": dest, "time": timestamp})
                _, ext = os.path.splitext(src)
                cat = helpers.get_category(ext)
                categories[cat] = categories.get(cat, 0) + 1
        elif line_str.startswith("REMOVED EMPTY FOLDER:"):
            folder = line_str.split("REMOVED EMPTY FOLDER:", 1)[1].strip()
            removed_dirs.append(folder)
        elif line_str.startswith("UNDONE:"):
            undone = True
            undone_at = line_str.split("UNDONE:", 1)[1].strip()
        elif line_str.startswith("STATUS: UNDONE"):
            undone = True
            if "at" in line_str:
                undone_at = line_str.split("at", 1)[1].strip()

    if not timestamp:
        try:
            mtime = os.path.getmtime(filepath)
            timestamp = datetime.fromtimestamp(mtime).isoformat()
        except OSError:
            timestamp = datetime.now().isoformat()

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "target_dir": target_dir,
        "deep": deep,
        "mode": mode,
        "total_files": len(moves),
        "categories": categories,
        "moves": moves,
        "removed_dirs": removed_dirs,
        "undone": undone,
        "undone_at": undone_at,
        "log_path": filepath
    }


def get_all_history() -> list:
    """Return all past transactions parsed from individual log files, newest first."""
    if not os.path.isdir(LOG_DIR):
        return []

    history_list = []
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".log") and (fname.startswith("run_") or "_" in fname):
            fpath = os.path.join(LOG_DIR, fname)
            record = parse_log_file(fpath)
            if record and (record["total_files"] > 0 or record["moves"] or record["target_dir"]):
                history_list.append(record)

    # Sort newest first by timestamp or mtime
    history_list.sort(key=lambda r: str(r.get("timestamp", "")), reverse=True)
    return history_list


def get_transaction(run_id: str) -> dict:
    """Retrieve a single transaction record from its log file by ID."""
    path = get_log_path(run_id)
    if os.path.isfile(path):
        return parse_log_file(path)
    return None


def undo_run(run_id: str) -> dict:
    """
    Reverse the moves recorded in a transaction's individual log file.
    Moves each file from 'dest' back to 'src'.
    Appends an UNDONE marker to the log file.
    Returns a summary dict {success: bool, restored: int, errors: list}.
    """
    target_item = get_transaction(run_id)
    if not target_item:
        return {
            "success": False,
            "message": "Run ID " + str(run_id) + " not found.",
            "restored": 0,
            "errors": []
        }

    if target_item.get("undone"):
        return {
            "success": False,
            "message": "Run ID " + str(run_id) + " was already undone.",
            "restored": 0,
            "errors": []
        }

    moves_list = target_item.get("moves", [])
    restored = 0
    errors = []

    for m in reversed(moves_list):
        src = m["src"]
        dest = m["dest"]

        if not os.path.exists(dest):
            errors.append("File at destination no longer exists: " + str(dest))
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
            errors.append("Failed to restore " + str(dest) + " -> " + str(src) + ": " + str(e))

    # Mark the log file as undone
    log_path = target_item.get("log_path")
    if log_path and os.path.exists(log_path):
        undo_timestamp = datetime.now().isoformat()
        undo_block = [
            "",
            "--- UNDO STATUS ---",
            "UNDONE: " + str(undo_timestamp),
            "STATUS: UNDONE at " + str(undo_timestamp),
            "Restored: " + str(restored) + "/" + str(len(moves_list)) + " files"
        ]
        if errors:
            undo_block.append("Errors encountered during rollback:")
            for err in errors:
                undo_block.append("  - " + str(err))
        write_log(log_path, "\n".join(undo_block))

    return {
        "success": len(errors) == 0,
        "restored": restored,
        "total_attempted": len(moves_list),
        "errors": errors,
        "message": "Restored " + str(restored) + "/" + str(len(moves_list)) + " files successfully."
    }
