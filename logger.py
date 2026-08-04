import os
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def start_log():
    """
    Create a new timestamped log file for this run and return its path.
    Called once at the start of a real (non-dry-run) clean.
    """
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, "run_" + timestamp + ".log")

    with open(log_path, "w") as log_file:
        log_file.write("Run started: " + str(datetime.now()) + "\n")

    return log_path


def write_log(log_path, message):
    """Append a single line to the given log file."""
    with open(log_path, "a") as log_file:
        log_file.write(message + "\n")