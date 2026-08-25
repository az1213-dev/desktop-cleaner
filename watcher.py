import os
import time
import threading
from os.path import splitext, join, isfile, dirname, basename
from shutil import move

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import config
from helpers import ensure_dir, make_unique, get_dest, get_category, format_bytes
from cleaner import is_category_folder
import history
from logger import start_log, write_log

IGNORE_EXTENSIONS = {".tmp", ".crdownload", ".part", ".download", ".partial", ".swp"}
IGNORE_PREFIXES = {"~$", ".", "#"}


class OrganizeEventHandler(FileSystemEventHandler):
    def __init__(self, watch_dir, deep=False, event_callback=None, debounce_secs=None):
        super().__init__()
        self.watch_dir = os.path.abspath(watch_dir)
        self.deep = deep
        self.event_callback = event_callback
        self.debounce_secs = debounce_secs or config.WATCHDOG_DEBOUNCE_SECONDS
        self._lock = threading.Lock()
        self._pending_files = {}

    def on_created(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._handle_file(event.dest_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file(event.src_path)

    def _handle_file(self, filepath):
        path = os.path.abspath(filepath)
        filename = basename(path)
        dirpath = dirname(path)

        parent_name = basename(dirpath)
        if is_category_folder(parent_name):
            return

        if not self.deep and dirpath != self.watch_dir:
            return

        _, ext = splitext(filename)
        ext_lower = ext.lower()

        if not ext or ext_lower in IGNORE_EXTENSIONS:
            return

        if any(filename.startswith(p) for p in IGNORE_PREFIXES):
            return

        with self._lock:
            timer = self._pending_files.get(path)
            if timer:
                timer.cancel()
            t = threading.Timer(self.debounce_secs, self._process_single_file, args=[path])
            self._pending_files[path] = t
            t.start()

    def _process_single_file(self, filepath):
        with self._lock:
            self._pending_files.pop(filepath, None)

        if not isfile(filepath):
            return

        filename = basename(filepath)
        _, ext = splitext(filename)
        ext_lower = ext.lower()

        if ext_lower in IGNORE_EXTENSIONS:
            return

        category = get_category(ext_lower)
        dest_dir = get_dest(ext_lower, self.watch_dir)
        ensure_dir(dest_dir)

        try:
            file_size = os.path.getsize(filepath)
        except OSError:
            file_size = 0

        unique_name = make_unique(dest_dir, filename)
        final_dest_path = join(dest_dir, unique_name)

        run_id = history.start_transaction(self.watch_dir, deep=self.deep, mode="watchdog")
        try:
            move(filepath, final_dest_path)
            history.record_move(run_id, filepath, final_dest_path)
            history.finish_transaction(run_id, {category: 1})

            file_info = {
                "name": filename,
                "src": filepath,
                "dest_path": final_dest_path,
                "category": category,
                "size": file_size,
                "size_formatted": format_bytes(file_size),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            if self.event_callback:
                self.event_callback({
                    "type": "watchdog_organized",
                    "file": file_info,
                    "target_dir": self.watch_dir,
                    "run_id": run_id
                })
        except Exception as e:
            if self.event_callback:
                self.event_callback({
                    "type": "watchdog_error",
                    "file": filename,
                    "error": str(e),
                    "target_dir": self.watch_dir
                })


class WatcherManager:
    def __init__(self):
        self._active_observers = {}
        self._lock = threading.Lock()

    def start(self, watch_dir, deep=False, event_callback=None):
        watch_path = os.path.abspath(watch_dir)
        with self._lock:
            if watch_path in self._active_observers:
                return False, "Already watching: " + str(watch_path)

            if not os.path.isdir(watch_path):
                return False, "Directory does not exist: " + str(watch_path)

            handler = OrganizeEventHandler(watch_path, deep=deep, event_callback=event_callback)
            observer = Observer()
            observer.schedule(handler, watch_path, recursive=deep)
            observer.start()
            self._active_observers[watch_path] = {
                "observer": observer,
                "handler": handler,
                "deep": deep,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            return True, "Started watching " + str(watch_path)

    def stop(self, watch_dir):
        watch_path = os.path.abspath(watch_dir)
        with self._lock:
            info = self._active_observers.pop(watch_path, None)
            if not info:
                return False, "Not currently watching: " + str(watch_path)

            info["observer"].stop()
            info["observer"].join(timeout=2.0)
            return True, "Stopped watching " + str(watch_path)

    def stop_all(self):
        with self._lock:
            for path, info in self._active_observers.items():
                info["observer"].stop()
                info["observer"].join(timeout=2.0)
            self._active_observers.clear()

    def list_active(self):
        with self._lock:
            return [
                {
                    "path": path,
                    "deep": info["deep"],
                    "started_at": info["started_at"]
                }
                for path, info in self._active_observers.items()
            ]


watcher_manager = WatcherManager()

