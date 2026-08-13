import os
import json

HOME = os.path.expanduser("~")

DOWNLOADS_DIR = os.path.join(HOME, "Downloads")

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

CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [MISC_CATEGORY]