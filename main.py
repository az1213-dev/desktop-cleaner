from config import DOWNLOADS_DIR
from cleaner import process_directory, summary_count
from helpers import get_available_drives


def show_menu():
    print("File Automation Tool")
    print("--------------------")
    print("1. Organize a Drive")
    print("2. Organize Downloads")
    print("3. Exit")
    print("")


def show_mode_menu():
    print("")
    print("1. Clean (move files)")
    print("2. Dry Run (preview only, no files moved)")
    print("3. Summary Only (counts only, no files moved)")
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


def confirm(message):
    answer = input(message + " (y/n): ").strip().lower()
    return answer == "y"


def run_mode(target_dir):
    """Ask which mode to run (clean / dry run / summary) against target_dir."""
    show_mode_menu()
    mode_choice = input("Choose a mode: ")

    if mode_choice == "1":
        preview = process_directory(target_dir, dry_run=True, quiet=True)
        total = sum(preview.values())

        if total == 0:
            print("No files to organize.")
            return

        if confirm("This will move " + str(total) + " file(s) in " + target_dir + ". Continue?"):
            process_directory(target_dir)
        else:
            print("Cancelled. No files were moved.")
    elif mode_choice == "2":
        process_directory(target_dir, dry_run=True)
    elif mode_choice == "3":
        summary_count(target_dir)
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
                run_mode(drive)
        elif choice == "2":
            run_mode(DOWNLOADS_DIR)
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again")

        print("")


if __name__ == "__main__":
    main()