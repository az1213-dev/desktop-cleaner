import os

HOME = os.path.expanduser("~")

# DOWNLOADS AND DESKTOP DIRECTORIES

SOURCE_DIR = os.path.join(HOME, "OneDrive", "Desktop")
DOWNLOADS_DIR = os.path.join(HOME, "Downloads")

# DESKTOP DIRECTORIES

DEST_DIR_IMAGES = os.path.join(SOURCE_DIR, "Images")
DEST_DIR_VIDEOS = os.path.join(SOURCE_DIR, "Videos")
DEST_DIR_AUDIO = os.path.join(SOURCE_DIR, "Audio")
DEST_DIR_DOCS = os.path.join(SOURCE_DIR, "Documents")
DEST_DIR_MISC = os.path.join(SOURCE_DIR, "Misc")

# DOWNLOADS DIRECTORIES

DL_IMAGES = os.path.join(DOWNLOADS_DIR, "Images")
DL_VIDEOS = os.path.join(DOWNLOADS_DIR, "Videos")
DL_AUDIO = os.path.join(DOWNLOADS_DIR, "Audio")
DL_DOCS = os.path.join(DOWNLOADS_DIR, "Documents")
DL_MISC = os.path.join(DOWNLOADS_DIR, "Misc")

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
