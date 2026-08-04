import os
import json

HOME = os.path.expanduser("~")

# SOURCE DIRECTORIES
# Note: there's no fixed "desktop" source anymore. The drive to organize
# is chosen interactively at runtime (see helpers.get_available_drives
# and main.select_drive). DOWNLOADS_DIR stays fixed since it's almost
# always the same known location.

DOWNLOADS_DIR = os.path.join(HOME, "Downloads")

# CATEGORY -> EXTENSIONS MAP
# Loaded from categories.json instead of being hardcoded here.
# Add new extensions by editing that file, not this one.

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(CONFIG_DIR, "categories.json")


def load_categories():
    try:
        with open(CATEGORIES_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: categories.json not found at " + CATEGORIES_FILE)
        raise
    except json.JSONDecodeError as e:
        print("Error: categories.json is not valid JSON.")
        print("Reason: " + str(e))
        raise

    categories = data.get("categories", {})
    misc_category = data.get("misc_category", "Misc")

    return categories, misc_category


CATEGORY_EXTENSIONS, MISC_CATEGORY = load_categories()

# Fixed order used for printing summaries so output is consistent
CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [MISC_CATEGORY]