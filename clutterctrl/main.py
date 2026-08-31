import sys
import os
import argparse
import time
from typing import Optional, List, Dict, Any

# Support both direct script execution (python clutterctrl/main.py) and module execution (python -m clutterctrl.main)
if __package__ is None or __package__ == "":
    _pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)
    __package__ = "clutterctrl"

from . import config
from .config import DOWNLOADS_DIR, reload_categories, CATEGORY_ORDER, CATEGORY_EXTENSIONS
from .cleaner import process_directory, deep_scan_directory
from .helpers import get_available_drives, get_quick_locations, format_bytes
from . import history
from .watcher import watcher_manager


# --- Terminal Colors & VT100 Setup ---
class Colors:
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def init_terminal():
    """Enable Windows 10+ ANSI color escape sequences and UTF-8 encoding."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            h_stdout = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
                kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)
        except Exception:
            pass


init_terminal()


def print_banner():
    c = Colors
    print(f"{c.CYAN}{c.BOLD}===================================================================={c.RESET}")
    print(f"{c.CYAN}{c.BOLD}                       C L U T T E R C T R L                        {c.RESET}")
    print(f"{c.CYAN}{c.BOLD}              Take control of your filesystem order                 {c.RESET}")
    print(f"{c.CYAN}{c.BOLD}===================================================================={c.RESET}")


def confirm(message: str) -> bool:
    c = Colors
    ans = input(f"{c.YELLOW}{message} (y/n): {c.RESET}").strip().lower()
    return ans in ("y", "yes")


def print_table(headers: List[str], rows: List[List[str]], col_align: Optional[List[str]] = None):
    """Render a clean formatted ASCII terminal table."""
    c = Colors
    if not rows:
        print(f"  {c.DIM}(No records found){c.RESET}")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Print Header
    header_str = " | ".join(f"{c.BOLD}{h.ljust(widths[i])}{c.RESET}" for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * widths[i] for i in range(len(headers)))
    print(f"  {header_str}")
    print(f"  {c.DIM}{sep_str}{c.RESET}")

    # Print Rows
    for row in rows:
        row_str = " | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row))
        print(f"  {row_str}")


def cmd_stats():
    """Display overall run log and lifetime organization statistics."""
    c = Colors
    stats = history.get_stats()
    print_banner()
    print(f"\n{c.BOLD}[*] System & Run History Statistics{c.RESET}")
    print(f"{c.DIM}Logs location: {stats['log_dir']} ({stats['total_log_files']} run log file(s)){c.RESET}\n")

    print(f"  * {c.BOLD}Total Runs Recorded:{c.RESET}       {c.CYAN}{stats['total_runs']}{c.RESET}")
    print(f"  * {c.BOLD}Active Files Organized:{c.RESET}    {c.GREEN}{stats['total_files_organized']}{c.RESET}")
    print(f"  * {c.BOLD}Active Data Organized:{c.RESET}     {c.GREEN}{stats['total_bytes_formatted']}{c.RESET}")
    print(f"  * {c.BOLD}Lifetime Files Moved:{c.RESET}      {c.WHITE}{stats['lifetime_files_moved']}{c.RESET}")
    print(f"  * {c.BOLD}Reverted (Undone) Runs:{c.RESET}    {c.YELLOW}{stats['total_undone_runs']}{c.RESET}\n")

    if stats["categories"]:
        print(f"{c.BOLD}Category Distribution:{c.RESET}")
        max_cnt = max((cat["count"] for cat in stats["categories"].values()), default=1) or 1
        for cat_name, cat_data in stats["categories"].items():
            bar_len = int((cat_data["count"] / max_cnt) * 24)
            bar = "#" * bar_len + "-" * (24 - bar_len)
            print(f"  {cat_name.ljust(18)} {c.CYAN}[{bar}]{c.RESET} {cat_data['count']:>4} files ({cat_data['bytes_formatted']})")
    print("")


def cmd_history(limit: int = 20):
    """Display recent run history from individual run log files."""
    c = Colors
    runs = history.get_all_history(limit=limit)
    print_banner()
    print(f"\n{c.BOLD}[*] Recent Organization Runs (Dedicated Log Files){c.RESET}\n")

    headers = ["#", "Run ID", "Date / Time", "Status", "Mode", "Files", "Size", "Target Folder"]
    rows = []
    for i, r in enumerate(runs, start=1):
        status_color = c.YELLOW if r["undone"] else c.GREEN
        status_text = f"{status_color}[UNDONE]{c.RESET}" if r["undone"] else f"{status_color}[ACTIVE]{c.RESET}"
        dt = r["timestamp"].replace("T", " ")[:19]
        deep_suffix = " (Deep)" if r["deep"] else ""
        target_str = r["target_dir"] + deep_suffix
        if len(target_str) > 35:
            target_str = "..." + target_str[-32:]

        rows.append([
            str(i),
            r["run_id"],
            dt,
            status_text,
            r["mode"],
            str(r["total_files"]),
            r["total_bytes_formatted"],
            target_str
        ])

    print_table(headers, rows)
    print(f"\n{c.DIM}To rollback any run: clutterctrl undo <Run ID>{c.RESET}\n")


def cmd_undo(run_id_or_index: Optional[str] = None):
    """Undo / Rollback a specific run or the latest active run."""
    c = Colors
    if not run_id_or_index:
        active_runs = [r for r in history.get_all_history(limit=10) if not r["undone"]]
        if not active_runs:
            print(f"{c.YELLOW}No active runs found in logs to undo.{c.RESET}")
            return
        target_run = active_runs[0]
    else:
        # Check if user passed an index number like '1' or '2'
        if run_id_or_index.isdigit():
            idx = int(run_id_or_index) - 1
            all_runs = history.get_all_history(limit=50)
            if 0 <= idx < len(all_runs):
                target_run = all_runs[idx]
            else:
                print(f"{c.RED}Invalid run index #{run_id_or_index}.{c.RESET}")
                return
        else:
            target_run = history.get_transaction(run_id_or_index)
            if not target_run:
                print(f"{c.RED}Run ID '{run_id_or_index}' not found in logs.{c.RESET}")
                return

    run_id = target_run["run_id"]
    if target_run.get("undone"):
        print(f"{c.YELLOW}Run '{run_id}' has already been undone.{c.RESET}")
        return

    print(f"\n{c.BOLD}[<] Rollback Run:{c.RESET} {c.CYAN}{run_id}{c.RESET}")
    print(f"  Target Directory: {target_run['target_dir']}")
    print(f"  Files to restore: {target_run['total_files']} files ({target_run.get('total_bytes_formatted', '')})")
    print(f"  Log File:         {target_run.get('log_path', '')}")

    if confirm("Are you sure you want to revert this operation?"):
        print(f"{c.DIM}Reverting files back to source locations...{c.RESET}")
        result = history.undo_run(run_id)
        if result["success"]:
            print(f"{c.GREEN}[OK] {result['message']}{c.RESET}\n")
        else:
            print(f"{c.RED}[ERR] {result['message']}{c.RESET}\n")
            for err in result.get("errors", []):
                print(f"  {c.RED}- {err}{c.RESET}")


def cmd_scan(target_dir: str, deep: bool = False):
    """Run a dry run scan and print a visual preview table."""
    c = Colors
    target = os.path.abspath(target_dir)
    if not os.path.isdir(target):
        print(f"{c.RED}Error: Directory not found: {target}{c.RESET}")
        return

    print_banner()
    print(f"\n{c.BOLD}[?] Dry Run Scan Preview:{c.RESET} {c.CYAN}{target}{c.RESET} {'(Deep Scan)' if deep else ''}\n")

    fn = deep_scan_directory if deep else process_directory
    res = fn(target, dry_run=True, quiet=True)

    files = res.get("files", [])
    if not files:
        print(f"{c.GREEN}No unorganized files found. Everything is already clean!{c.RESET}\n")
        return

    headers = ["#", "File Name", "Category", "Size", "Destination Subfolder"]
    rows = []
    for i, f in enumerate(files[:50], start=1):
        rows.append([
            str(i),
            f["name"] if len(f["name"]) <= 30 else f["name"][:27] + "...",
            f["category"],
            f["size_formatted"],
            os.path.basename(f["dest_dir"])
        ])

    print_table(headers, rows)
    if len(files) > 50:
        print(f"\n  {c.DIM}... and {len(files) - 50} more file(s){c.RESET}")

    print(f"\n{c.BOLD}Summary:{c.RESET} {c.CYAN}{res['total_files']} files{c.RESET} ({res['total_bytes_formatted']}) would be organized.")
    for cat, cnt in res["counts"].items():
        if cnt > 0:
            print(f"  * {cat.ljust(15)}: {cnt}")
    print(f"\n{c.DIM}To execute this cleanup: clutterctrl clean \"{target}\"{' --deep' if deep else ''}{c.RESET}\n")


def cmd_clean(target_dir: str, deep: bool = False, quiet: bool = False):
    """Execute live file organization and record into dedicated run log file."""
    c = Colors
    target = os.path.abspath(target_dir)
    if not os.path.isdir(target):
        print(f"{c.RED}Error: Directory not found: {target}{c.RESET}")
        return

    print_banner()
    print(f"\n{c.BOLD}[+] ClutterCtrl Organizing:{c.RESET} {c.CYAN}{target}{c.RESET} {'(Deep Scan)' if deep else ''}\n")

    fn = deep_scan_directory if deep else process_directory
    res = fn(target, dry_run=False, quiet=quiet)

    print(f"\n{c.GREEN}[OK] Organization Complete!{c.RESET}")
    print(f"  * Total Files Moved: {c.BOLD}{res['total_files']}{c.RESET} ({res['total_bytes_formatted']})")
    print(f"  * Run ID:            {c.CYAN}{res['run_id']}{c.RESET}")
    print(f"  * Log File:          {res.get('log_path', '')}")
    if res.get("removed_dirs"):
        print(f"  * Empty Folders Removed: {len(res['removed_dirs'])}")
    print(f"\n{c.DIM}To rollback this run anytime: clutterctrl undo {res['run_id']}{c.RESET}\n")


def cmd_watch(target_dir: str, deep: bool = False):
    """Start background folder watcher in the terminal."""
    c = Colors
    target = os.path.abspath(target_dir)
    if not os.path.isdir(target):
        print(f"{c.RED}Error: Directory not found: {target}{c.RESET}")
        return

    print_banner()
    print(f"\n{c.BOLD}[*] Active Folder Watcher Started{c.RESET}")
    print(f"  Monitoring Directory: {c.CYAN}{target}{c.RESET}")
    print(f"  Recursive (Deep):     {c.WHITE}{deep}{c.RESET}")
    print(f"  Audit Logging:        {c.GREEN}Dedicated Run Logs{c.RESET}")
    print(f"  {c.DIM}Press Ctrl+C to stop watcher.{c.RESET}\n")

    def on_event(event):
        if event["type"] == "watchdog_organized":
            f = event["file"]
            print(f"{c.GREEN}[AUTO-SORTED]{c.RESET} {c.WHITE}{f['name']}{c.RESET} -> {c.CYAN}{f['category']}{c.RESET} ({f['size_formatted']})")
        elif event["type"] == "watchdog_error":
            print(f"{c.RED}[ERROR]{c.RESET} {event['file']}: {event['error']}")

    success, msg = watcher_manager.start(target, deep=deep, event_callback=on_event)
    if not success:
        print(f"{c.RED}Error: {msg}{c.RESET}")
        return

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{c.YELLOW}Stopping watcher...{c.RESET}")
        watcher_manager.stop(target)
        print(f"{c.GREEN}Watcher stopped safely.{c.RESET}\n")


def cmd_rules():
    """Display current category extension rules."""
    c = Colors
    categories, misc = config.load_categories()
    print_banner()
    print(f"\n{c.BOLD}[*] Category Extension Mappings{c.RESET} {c.DIM}({config.CATEGORIES_FILE}){c.RESET}\n")

    headers = ["Category", "Total Extensions", "Sample Extensions"]
    rows = []
    for cat_name, exts in categories.items():
        sample = ", ".join(exts[:8])
        if len(exts) > 8:
            sample += f" ... (+{len(exts) - 8} more)"
        rows.append([cat_name, str(len(exts)), sample])
    rows.append([misc, "-", "Any unrecognized extensions"])

    print_table(headers, rows)
    print("")


def select_target_menu() -> Optional[str]:
    """Helper menu to select a target path from quick locations or custom input."""
    c = Colors
    locs = get_quick_locations()
    print(f"\n{c.BOLD}Select a Location to Organize:{c.RESET}")
    for i, loc in enumerate(locs, start=1):
        print(f"  {c.CYAN}{i}.{c.RESET} {loc['name'].ljust(18)} {c.DIM}({loc['path']}){c.RESET}")
    print(f"  {c.CYAN}{len(locs) + 1}.{c.RESET} Custom Directory Path...")
    print(f"  {c.CYAN}0.{c.RESET} Back to Main Menu")

    choice = input(f"\n{c.YELLOW}Choose location (number): {c.RESET}").strip()
    if choice == "0" or not choice:
        return None

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(locs):
            return locs[idx]["path"]
        elif idx == len(locs):
            custom_path = input(f"{c.YELLOW}Enter full directory path: {c.RESET}").strip()
            if os.path.isdir(custom_path):
                return custom_path
            print(f"{c.RED}Invalid directory path.{c.RESET}")
            return None
    except ValueError:
        pass

    print(f"{c.RED}Invalid selection.{c.RESET}")
    return None


def select_scan_type_menu() -> bool:
    """Prompt for standard vs deep scan."""
    c = Colors
    print(f"\n{c.BOLD}Choose Scan Mode:{c.RESET}")
    print(f"  {c.CYAN}1.{c.RESET} Standard (Top-level files only)")
    print(f"  {c.CYAN}2.{c.RESET} Deep Scan (Recursive subfolders + cleanup empty directories)")
    choice = input(f"{c.YELLOW}Choice [1]: {c.RESET}").strip()
    return choice == "2"


def interactive_menu():
    """Main interactive terminal loop for Windows CMD / Terminal."""
    c = Colors
    while True:
        print_banner()
        print(f"  {c.CYAN}1.{c.RESET} [+] Organize / Clean a Folder")
        print(f"  {c.CYAN}2.{c.RESET} [?] Dry Run Preview (Scan without moving)")
        print(f"  {c.CYAN}3.{c.RESET} [*] Start Live Background Watcher")
        print(f"  {c.CYAN}4.{c.RESET} [=] Run History & 1-Click Rollback")
        print(f"  {c.CYAN}5.{c.RESET} [%] Storage & Lifetime Statistics")
        print(f"  {c.CYAN}6.{c.RESET} [@] Category Extension Rules")
        print(f"  {c.CYAN}7.{c.RESET} [X] Exit\n")

        choice = input(f"{c.YELLOW}Select an option [1-7]: {c.RESET}").strip()

        if choice == "1":
            target = select_target_menu()
            if target:
                deep = select_scan_type_menu()
                cmd_clean(target, deep=deep)
        elif choice == "2":
            target = select_target_menu()
            if target:
                deep = select_scan_type_menu()
                cmd_scan(target, deep=deep)
        elif choice == "3":
            target = select_target_menu()
            if target:
                deep = select_scan_type_menu()
                cmd_watch(target, deep=deep)
        elif choice == "4":
            cmd_history(limit=15)
            sub_choice = input(f"{c.YELLOW}Enter Run # or Run ID to undo (or press Enter to return): {c.RESET}").strip()
            if sub_choice:
                cmd_undo(sub_choice)
        elif choice == "5":
            cmd_stats()
        elif choice == "6":
            cmd_rules()
        elif choice in ("7", "8", "q", "exit"):
            print(f"\n{c.CYAN}Clutter controlled. Goodbye!{c.RESET}\n")
            break
        else:
            print(f"\n{c.RED}Invalid option. Please choose 1-7.{c.RESET}\n")

        input(f"\n{c.DIM}Press Enter to continue...{c.RESET}")
        print("\n" * 2)


def main():
    parser = argparse.ArgumentParser(
        prog="clutterctrl",
        description="ClutterCtrl: Lightweight File Organizer with Per-Run Audit Logs & Rollback"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # clean subcommand
    clean_p = subparsers.add_parser("clean", help="Organize files in target directory")
    clean_p.add_argument("target", nargs="?", default=DOWNLOADS_DIR, help="Target folder (default: Downloads)")
    clean_p.add_argument("--deep", "-d", action="store_true", help="Recursive deep scan")
    clean_p.add_argument("--quiet", "-q", action="store_true", help="Summary output only")

    # scan / dry-run subcommand
    scan_p = subparsers.add_parser("scan", help="Preview organization without moving files")
    scan_p.add_argument("target", nargs="?", default=DOWNLOADS_DIR, help="Target folder (default: Downloads)")
    scan_p.add_argument("--deep", "-d", action="store_true", help="Recursive deep scan")

    # watch subcommand
    watch_p = subparsers.add_parser("watch", help="Watch folder for new files and auto-sort")
    watch_p.add_argument("target", nargs="?", default=DOWNLOADS_DIR, help="Target folder (default: Downloads)")
    watch_p.add_argument("--deep", "-d", action="store_true", help="Recursive deep scan")

    # history subcommand
    hist_p = subparsers.add_parser("history", help="List past organization runs from log files")
    hist_p.add_argument("--limit", "-n", type=int, default=20, help="Number of runs to display")

    # undo subcommand
    undo_p = subparsers.add_parser("undo", help="Rollback / undo a specific run")
    undo_p.add_argument("run_id", nargs="?", default=None, help="Run ID or index # (default: latest active run)")

    # stats subcommand
    subparsers.add_parser("stats", help="Show storage and lifetime organization statistics")

    # rules subcommand
    subparsers.add_parser("rules", help="Show category extension mappings")

    # Legacy / Flag-based arguments for backwards compatibility
    parser.add_argument("--target", "-t", type=str, help="Target directory")
    parser.add_argument("--clean", action="store_true", help="Clean immediately")
    parser.add_argument("--dry-run", action="store_true", help="Dry run preview")
    parser.add_argument("--deep", action="store_true", help="Recursive deep scan")
    parser.add_argument("--watch", "-w", type=str, help="Watch directory")
    parser.add_argument("--undo", type=str, help="Undo run ID")
    parser.add_argument("--undo-last", action="store_true", help="Undo last run")

    args = parser.parse_args()

    # Handle Subcommands
    if args.command == "clean":
        cmd_clean(args.target, deep=args.deep, quiet=args.quiet)
    elif args.command == "scan":
        cmd_scan(args.target, deep=args.deep)
    elif args.command == "watch":
        cmd_watch(args.target, deep=args.deep)
    elif args.command == "history":
        cmd_history(limit=args.limit)
    elif args.command == "undo":
        cmd_undo(args.run_id)
    elif args.command == "stats":
        cmd_stats()
    elif args.command == "rules":
        cmd_rules()

    # Handle Legacy Flags
    elif args.watch:
        cmd_watch(args.watch, deep=args.deep)
    elif args.undo:
        cmd_undo(args.undo)
    elif args.undo_last:
        cmd_undo(None)
    elif args.target:
        if args.clean:
            cmd_clean(args.target, deep=args.deep)
        else:
            cmd_scan(args.target, deep=args.deep)
    else:
        # Launch Interactive Terminal Menu
        interactive_menu()


if __name__ == "__main__":
    main()