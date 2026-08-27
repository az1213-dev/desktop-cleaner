import os
import json

# Load environment variables from .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    pkg_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(root_env):
        load_dotenv(root_env)
    elif os.path.exists(pkg_env):
        load_dotenv(pkg_env)
    else:
        load_dotenv()
except ImportError:
    pass

# User Directories
HOME = os.path.expanduser("~")
DOWNLOADS_DIR = os.path.join(HOME, "Downloads")
DESKTOP_DIR = os.path.join(HOME, "Desktop")
DOCUMENTS_DIR = os.path.join(HOME, "Documents")
PICTURES_DIR = os.path.join(HOME, "Pictures")
VIDEOS_DIR = os.path.join(HOME, "Videos")
MUSIC_DIR = os.path.join(HOME, "Music")

# Application Configuration
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CATEGORIES_FILE = os.path.join(CONFIG_DIR, "categories.json")

# Server & Security Settings
APP_ENV = os.getenv("APP_ENV", "production")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
SECRET_KEY = os.getenv("SECRET_KEY", "default-insecure-secret-key-please-change")
ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",") if origin.strip()
]
WATCHDOG_DEBOUNCE_SECONDS = float(os.getenv("WATCHDOG_DEBOUNCE_SECONDS", "2.0"))
AUTO_OPEN_BROWSER = os.getenv("AUTO_OPEN_BROWSER", "true").lower() in ("true", "1", "yes")


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