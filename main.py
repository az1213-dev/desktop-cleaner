import sys
import os
import argparse
import webbrowser
import threading
import time

from config import DOWNLOADS_DIR, reload_categories
from cleaner import process_directory, deep_scan_directory
from helpers import get_available_drives, format_bytes
import history
from watcher import watcher_manager


def show_menu():
    print("========================================")
    print("             T I D E W A Y              ")
    print("   Sweep your files into order.         ")
    print("========================================")
    print("1. Organize a Drive")
    print("2. Organize Downloads")
    print("3. Launch Real-Time Web Dashboard")
    print("4. Run History & Undo / Rollback")
    print("5. Start Background Folder Watcher")
    print("6. Exit")
    print("")


def show_scan_type_menu():
    print("")
    print("1. Standard (top-level files only)")
    print("2. Deep Scan (all subfolders, recursively)")
    print("")


def show_mode_menu():
    print("")
    print("1. Clean (move files)")
    print("2. Dry Run (preview only, nothing changed)")
    print("3. Summary Only (counts only, nothing changed)")
    print("4. Back")
    print("")


def select_drive():
    """List detected drives and let the user pick one."""
    drives = get_available_drives()

    if not drives:
        print("No drives detected.")
        return None

    print("")
    print("Available drives:")
    for i, drive in enumerate(drives, start=1):
        print(str(i) + ". " + str(drive))
    print("")

    choice = input("Select a drive to organize (number): ")

    try:
        index = int(choice) - 1
    except ValueError:
        print("Invalid selection.")
        return None

    if 0 <= index < len(drives):
        return drives[index]

    print("Invalid selection.")
    return None


def select_scan_type():
    """Returns True for deep scan, False for standard."""
    show_scan_type_menu()
    choice = input("Choose scan type: ")
    return choice == "2"


def confirm(message):
    answer = input(message + " (y/n): ").strip().lower()
    return answer == "y"


def run_mode(target_dir, deep=False):
    """Ask which mode to run (clean / dry run / summary) against target_dir."""
    scan_func = deep_scan_directory if deep else process_directory

    show_mode_menu()
    mode_choice = input("Choose a mode: ")

    if mode_choice == "1":
        preview = scan_func(target_dir, dry_run=True, quiet=True)
        total = preview.get("total_files", 0)

        if total == 0:
            print("No files to organize.")
            return

        message = "This will move " + str(total) + " file(s) in " + str(target_dir)
        if deep:
            message += " and remove any subfolders left empty afterward"
        message += ". Continue?"

        if confirm(message):
            scan_func(target_dir, dry_run=False)
        else:
            print("Cancelled. No files were moved.")
    elif mode_choice == "2":
        scan_func(target_dir, dry_run=True)
    elif mode_choice == "3":
        scan_func(target_dir, dry_run=True, quiet=True)
    elif mode_choice == "4":
        return
    else:
        print("Invalid choice.")


def show_history_menu():
    runs = history.get_all_history()
    if not runs:
        print("\nNo previous runs found in history.\n")
        return

    print("\nRecent Runs:")
    print("----------------------------------------------------------------------")
    for i, r in enumerate(runs[:10], start=1):
        status = "[REVERTED]" if r.get("undone") else "[ACTIVE]"
        date_str = r.get("timestamp", "").replace("T", " ")[:19]
        files = r.get("total_files", 0)
        deep_str = " (Deep)" if r.get("deep") else ""
        print(str(i) + ". " + str(r['run_id']) + " " + status + " - " + date_str + " - " + str(files) + " files - " + str(r['target_dir']) + deep_str)
    print("----------------------------------------------------------------------")

    choice = input("Enter run number to Undo / Rollback (or Enter to go back): ").strip()
    if not choice:
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(runs[:10]):
            target_run = runs[idx]
            if target_run.get("undone"):
                print("This run has already been undone.")
                return
            if confirm("Are you sure you want to revert run " + str(target_run['run_id']) + "?"):
                result = history.undo_run(target_run["run_id"])
                print(result["message"])
        else:
            print("Invalid run number.")
    except ValueError:
        print("Invalid selection.")


def launch_dashboard(port=8000, open_browser=True):
    print("\n[+] Launching File Organizer Web Dashboard on http://localhost:" + str(port) + " ...")
    
    def open_tab():
        time.sleep(1.2)
        if open_browser:
            webbrowser.open("http://localhost:" + str(port))

    threading.Thread(target=open_tab, daemon=True).start()

    from dashboard.server import run_server
    try:
        run_server(host="127.0.0.1", port=port)
    except KeyboardInterrupt:
        print("\nDashboard stopped.")


def run_cli_watcher(target_dir, deep=False):
    print("\nStarting Background Folder Watcher on: " + str(target_dir) + " (Deep=" + str(deep) + ")")
    print("Press Ctrl+C to stop.\n")
    
    def on_event(event):
        if event["type"] == "watchdog_organized":
            f = event["file"]
            print("[WATCHER AUTO-MOVE] " + str(f['name']) + " -> " + str(f['dest_path']) + " (" + str(f['size_formatted']) + ")")
        elif event["type"] == "watchdog_error":
            print("[WATCHER ERROR] " + str(event['file']) + ": " + str(event['error']))

    success, msg = watcher_manager.start(target_dir, deep=deep, event_callback=on_event)
    if not success:
        print("Error: " + str(msg))
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher_manager.stop_all()
        print("Watcher stopped.")


def main():
    parser = argparse.ArgumentParser(description="File Organizer & Automation Suite")
    parser.add_argument("--dashboard", "-d", action="store_true", help="Launch real-time web dashboard")
    parser.add_argument("--port", type=int, default=8000, help="Web dashboard port (default: 8000)")
    parser.add_argument("--watch", "-w", type=str, help="Watch and auto-organize a directory in background")
    parser.add_argument("--deep", action="store_true", help="Enable recursive deep scan")
    parser.add_argument("--target", "-t", type=str, help="Directory to organize")
    parser.add_argument("--clean", action="store_true", help="Run clean immediately on target")
    parser.add_argument("--dry-run", action="store_true", help="Run dry-run preview on target")
    parser.add_argument("--undo", type=str, help="Undo a specific run ID")
    parser.add_argument("--undo-last", action="store_true", help="Undo the most recent run")

    args = parser.parse_args()

    if args.dashboard:
        launch_dashboard(port=args.port)
        return

    if args.watch:
        run_cli_watcher(args.watch, deep=args.deep)
        return

    if args.undo:
        res = history.undo_run(args.undo)
        print(res["message"])
        return

    if args.undo_last:
        runs = [r for r in history.get_all_history() if not r.get("undone")]
        if not runs:
            print("No active runs to undo.")
            return
        res = history.undo_run(runs[0]["run_id"])
        print(res["message"])
        return

    if args.target:
        target = os.path.abspath(args.target)
        if args.clean:
            fn = deep_scan_directory if args.deep else process_directory
            fn(target, dry_run=False)
        else:
            fn = deep_scan_directory if args.deep else process_directory
            fn(target, dry_run=True)
        return

    # Interactive Terminal Menu
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            drive = select_drive()
            if drive:
                deep = select_scan_type()
                run_mode(drive, deep=deep)
        elif choice == "2":
            deep = select_scan_type()
            run_mode(DOWNLOADS_DIR, deep=deep)
        elif choice == "3":
            launch_dashboard()
        elif choice == "4":
            show_history_menu()
        elif choice == "5":
            target = input("Enter folder path to watch [" + str(DOWNLOADS_DIR) + "]: ").strip()
            if not target:
                target = DOWNLOADS_DIR
            deep = confirm("Enable deep recursive scanning for subfolders?")
            run_cli_watcher(target, deep=deep)
        elif choice == "6":
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Try again.\n")

        print("")


if __name__ == "__main__":
    main()