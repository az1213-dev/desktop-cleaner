from desktop_cleaner import clean_desktop
from downloads_cleaner import clean_downloads
from summary import summary_count

from config import SOURCE_DIR, DOWNLOADS_DIR

def show_menu():
    print("File Automation Tool")
    print("--------------------")
    print("1. Clean Desktop")
    print("2. Clean Downloads")
    print("3. Summary Only (Desktop)")
    print("4. Summary Only (Downloads)")
    print("5. Exit")
    print("")

# MAIN FUNCTION AND RUNGUARD

def main():
    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            clean_desktop()
        elif choice == "2":
            clean_downloads()
        elif choice == "3":
            summary_count(SOURCE_DIR)
        elif choice == "4":
            summary_count(DOWNLOADS_DIR)
        elif choice == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again")
            print("")

if __name__ == "__main__":
    main()