import os
import uuid
import logging
from datetime import datetime

from . import config

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# Configure logger level
logger = logging.getLogger("tideway")
logging.basicConfig(level=getattr(logging, getattr(config, "LOG_LEVEL", "INFO"), logging.INFO))


def prune_old_logs(max_files=None):
    """Keep only the most recent N log files to manage disk usage."""
    limit = max_files if max_files is not None else getattr(config, "MAX_LOG_FILES", 50)
    if limit <= 0 or not os.path.isdir(LOG_DIR):
        return

    log_files = []
    for fname in os.listdir(LOG_DIR):
        if fname.endswith(".log"):
            fpath = os.path.join(LOG_DIR, fname)
            try:
                log_files.append((fpath, os.path.getmtime(fpath)))
            except OSError:
                pass

    if len(log_files) > limit:
        # Sort oldest first
        log_files.sort(key=lambda item: item[1])
        excess = len(log_files) - limit
        for fpath, _ in log_files[:excess]:
            try:
                os.remove(fpath)
            except OSError:
                pass


def start_log(target_dir="", deep=False, mode="clean", run_id=None):
    """
    Create a new timestamped log file for this run and return its path.
    Called once at the start of a real (non-dry-run) clean or transaction.
    """
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    prune_old_logs()

    if not run_id:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = "run_" + timestamp + "_" + str(uuid.uuid4().hex[:6])

    log_filename = (run_id + ".log") if not run_id.endswith(".log") else run_id
    log_path = os.path.join(LOG_DIR, log_filename)

    with open(log_path, "w", encoding="utf-8") as log_file:
        log_file.write("Run ID: " + str(run_id) + "\n")
        log_file.write("Run started: " + str(datetime.now().isoformat()) + "\n")
        if target_dir:
            log_file.write("Target: " + str(target_dir) + "\n")
        log_file.write("Deep Scan: " + str(deep) + "\n")
        log_file.write("Mode: " + str(mode) + "\n")
        log_file.write("Status: ACTIVE\n\n")
        log_file.write("--- OPERATIONS ---\n")

    return log_path


def write_log(log_path, message):
    """Append a single line to the given log file."""
    if not log_path:
        return
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(str(message) + "\n")