import os 
from os import scandir
from os.path import splitext, exists, join
from shutil import move

# CONFIGURATION

SOURCE_DIR = "/Users/azapa/Desktop" 

DEST_DIR_IMAGES = "/Users/azapa/Desktop/Images"
DEST_DIR_VIDEOS = "/Users/azapa/Desktop/Images"
DEST_DIR_AUDIO = "/Users/azapa/Desktop/Audio"
DEST_DIR_DOCS = "/Users/azapa/Desktop/Documents"
DEST_DIR_MISC = "/Users/azapa/Desktop/Misc"

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

    with scandir(SOURCE_DIR) as entries:
        for entry in entries:
            if entry.is_file():
                _, ext = splitext(entry.name)
                if not ext: continue

                dest_dir = get_dest(ext)
                ensure_dir(dest_dir)

                unique_name = make_unique(dest_dir, entry.name)
                dest_path = join(dest_dir, unique_name)

                print("Moving " + entry.name + "to" + dest_dir)
                move(entry.path, dest_path)

    print("Cleaning complete.")

# MAIN FUNCTION AND RUNGUARD

def main():
    clean_desktop()

if __name__ == "__main__":
    main()