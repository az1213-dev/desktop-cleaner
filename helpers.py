import os
import platform
import string
from os.path import splitext, exists, join

from config import CATEGORY_EXTENSIONS, MISC_CATEGORY


def get_available_drives():
    """
    Return a list of available drive/mount roots to choose from.

    On Windows: queries GetLogicalDrives() and returns things like
    ['C:\\', 'D:\\', 'T:\\'] for every drive letter currently in use
    (local disks, removable drives, and mapped network drives).

    On macOS/Linux: falls back to '/' plus anything mounted under
    '/mnt' or '/Volumes', since there's no drive-letter concept there.
    """
    drives = []

    if platform.system() == "Windows":
        import ctypes

        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drives.append(letter + ":\\")
    else:
        candidates = ["/"]
        for mount_root in ("/mnt", "/Volumes"):
            if os.path.isdir(mount_root):
                candidates += [
                    join(mount_root, name) for name in os.listdir(mount_root)
                ]
        drives = [d for d in candidates if os.path.isdir(d)]

    return drives


def ensure_dir(path):
    """Create the directory (and parents) if it doesn't already exist."""
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def make_unique(dest_dir, name):
    """Return a filename that doesn't collide with anything in dest_dir."""
    filename, extension = splitext(name)
    count = 1
    new_name = name

    while exists(join(dest_dir, new_name)):
        new_name = filename + "_" + str(count) + extension
        count += 1

    return new_name


def get_category(extension):
    """Map a file extension to a category name, e.g. '.png' -> 'Images'."""
    ext = extension.lower()

    for category, extensions in CATEGORY_EXTENSIONS.items():
        if ext in extensions:
            return category

    return MISC_CATEGORY


def get_dest(extension, base_dir):
    """
    Return the destination folder for a file with this extension,
    rooted under base_dir (works for both SOURCE_DIR and DOWNLOADS_DIR).
    """
    category = get_category(extension)
    return os.path.join(base_dir, category)