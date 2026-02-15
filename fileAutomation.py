import os 
from os import scandir
from os.path import splitext, exists, join
from shutil import move

# CONFIGURATION

SOURCE_DIR = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")

DEST_DIR_IMAGES = os.path.join(SOURCE_DIR, "Images")
DEST_DIR_VIDEOS = os.path.join(SOURCE_DIR, "Videos")
DEST_DIR_AUDIO = os.path.join(SOURCE_DIR, "Audio")
DEST_DIR_DOCS = os.path.join(SOURCE_DIR, "Documents")
DEST_DIR_MISC = os.path.join(SOURCE_DIR, "Misc")

IMAGE_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".bmp", ".heic"
]

VIDEO_EXTENSIONS = [
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"
]

AUDIO_EXTENSIONS = [
    ".mp3", ".wav", ".aac", ".m4a", ".flac"
]

DOC_EXTENSIONS = [
    ".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"
]   

# HELPER FUNCTIONS

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path,exist_ok=True) 

def make_unique(dest_dir, name):
    filename, extension = splitext(name)
    count = 1
    new_name = name

    while exists(join(dest_dir,new_name)):
        new_name = filename + "_" + str(count) + extension
        count += 1
    
    return new_name

def get_dest(extension):
    ext = extension.lower()

    if ext in IMAGE_EXTENSIONS:
        return DEST_DIR_IMAGES
    if ext in VIDEO_EXTENSIONS:
        return DEST_DIR_VIDEOS
    if ext in AUDIO_EXTENSIONS:
        return DEST_DIR_AUDIO
    if ext in DOC_EXTENSIONS:
        return DEST_DIR_DOCS
    
    return DEST_DIR_MISC

# CLEAN DESKTOP FUNCTION

def clean_desktop():
    print("Scanning " + SOURCE_DIR)

    files_moved = 0
    moved_imgs = 0
    moved_videos = 0 
    moved_audio = 0
    moved_docs = 0
    moved_misc = 0

    try:
        with scandir(SOURCE_DIR) as entries:
            for entry in entries:
                if entry.is_file():
                    _, ext = splitext(entry.name)
                    if not ext: continue

                    dest_dir = get_dest(ext)
                    ensure_dir(dest_dir)

                    unique_name = make_unique(dest_dir, entry.name)
                    dest_path = join(dest_dir, unique_name)

                    try:
                        print("Moving " + entry.name + " to " + dest_dir)
                        move(entry.path, dest_path)
                        files_moved += 1

                        if dest_dir == DEST_DIR_IMAGES:
                            moved_imgs += 1
                        elif dest_dir == DEST_DIR_VIDEOS:
                            moved_videos += 1
                        elif dest_dir == DEST_DIR_AUDIO:
                            moved_audio += 1
                        elif dest_dir == DEST_DIR_DOCS:
                            moved_docs += 1
                        else:
                            moved_misc += 1
                    
                    except Exception as e:
                        print("Error moving file: " + entry.name)
                        print("Reason: " + str(e))

    except Exception as e:
        print("Error scanning desktop")
        print("Reason: "+ str(e))
        return

    print("Cleaning complete.")
    print("Total files moved: " + str(files_moved))
    print("Images: " + str(moved_imgs))
    print("Videos: " + str(moved_videos))
    print("Audio: " + str(moved_audio))
    print("Documents: " + str(moved_docs))
    print("Misc: " + str(moved_misc))

# TERMINAL MENU

def show_menu():
    print("Desktop Cleaner")
    print("---------------")
    print("1. Clean Desktop")
    print("2. Exit")
    print("")

# MAIN FUNCTION AND RUNGUARD

def main():
    while True:
        show_menu()
        choice = input("Choose an option: ")

        if choice == "1":
            clean_desktop()
        elif choice == "2":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again")
            print("")

if __name__ == "__main__":
    main()