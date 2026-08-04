import os

HOME = os.path.expanduser("~")

# SOURCE DIRECTORIES
# Note: there's no fixed "desktop" source anymore. The drive to organize
# is chosen interactively at runtime (see helpers.get_available_drives
# and main.select_drive). DOWNLOADS_DIR stays fixed since it's almost
# always the same known location.

DOWNLOADS_DIR = os.path.join(HOME, "Downloads")

# CATEGORY -> EXTENSIONS MAP
# Add new extensions here and they'll automatically be picked up
# by get_category() / get_dest() in helpers.py.

CATEGORY_EXTENSIONS = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".bmp", ".heic"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"],
    "Audio": [".mp3", ".wav", ".aac", ".m4a", ".flac"],
    "Documents": [".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"],
}

MISC_CATEGORY = "Misc"

# Fixed order used for printing summaries so output is consistent
CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [MISC_CATEGORY]