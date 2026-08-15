from config import DOWNLOADS_DIR
from cleaner import process_directory, deep_scan_directory
from helpers import get_available_drives


def show_menu():
    print("File Automation Tool")
    print("--------------------")
    print("1. Organize a Drive")
    print("2. Organize Downloads")
    print("3. Exit")
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
    """List detected drives and let the user pick one. Returns the drive
    root (e.g. 'C:\\') or None if nothing valid was selected."""
    drives = get_available_drives()

    if not drives:
        print("No drives detected.")
        return None

    print("")
    print("Available drives:")
    for i, drive in enumerate(drives, start=1):
        print(str(i) + ". " + drive)
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
    """Ask which mode to run (clean / dry run / summary) against target_dir,
    using either the standard or deep-scan function depending on `deep`."""
    scan_func = deep_scan_directory if deep else process_directory

    show_mode_menu()
    mode_choice = input("Choose a mode: ")

    if mode_choice == "1":
        preview = scan_func(target_dir, dry_run=True, quiet=True)
        total = sum(preview.values())

        if total == 0:
            print("No files to organize.")
            return

        message = "This will move " + str(total) + " file(s) in " + target_dir
        if deep:
            message += " and remove any subfolders left empty afterward"
        message += ". Continue?"

        if confirm(message):
            scan_func(target_dir)
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


def main():
    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            drive = select_drive()
            if drive:
                deep = select_scan_type()
                run_mode(drive, deep=deep)
        elif choice == "2":
            deep = select_scan_type()
            run_mode(DOWNLOADS_DIR, deep=deep)
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again")

        print("")


if __name__ == "__main__":
    main()