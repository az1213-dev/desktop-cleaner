import os
import json

# User Standard Folders
HOME = os.path.expanduser("~")
DOWNLOADS_DIR = os.path.join(HOME, "Downloads")
DESKTOP_DIR = os.path.join(HOME, "Desktop")
DOCUMENTS_DIR = os.path.join(HOME, "Documents")
PICTURES_DIR = os.path.join(HOME, "Pictures")
VIDEOS_DIR = os.path.join(HOME, "Videos")
MUSIC_DIR = os.path.join(HOME, "Music")

# Application Configuration & Category Rules
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(CONFIG_DIR, "categories.json")

# Run Logs Directory (inside clutterctrl package/repository)
LOG_DIR = os.getenv("CLUTTERCTRL_LOG_DIR", os.path.join(CONFIG_DIR, "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

# Watcher Configuration
WATCHDOG_DEBOUNCE_SECONDS = float(os.getenv("WATCHDOG_DEBOUNCE_SECONDS", "2.0"))
MAX_LOG_FILES = int(os.getenv("MAX_LOG_FILES", "100"))


def load_categories():
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
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


def save_categories(categories_dict, misc="Misc"):
    data = {
        "categories": categories_dict,
        "misc_category": misc
    }
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    reload_categories()


def reload_categories():
    global CATEGORY_EXTENSIONS, MISC_CATEGORY, CATEGORY_ORDER
    CATEGORY_EXTENSIONS, MISC_CATEGORY = load_categories()
    CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [MISC_CATEGORY]
    return CATEGORY_EXTENSIONS, MISC_CATEGORY, CATEGORY_ORDER


CATEGORY_EXTENSIONS, MISC_CATEGORY = load_categories()
CATEGORY_ORDER = list(CATEGORY_EXTENSIONS.keys()) + [MISC_CATEGORY]