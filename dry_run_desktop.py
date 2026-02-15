from config import SOURCE_DIR
from os import scandir
from os.path import splitext
from helpers import get_dest

def dry_run():
    print("Dry Run: Scanning " + SOURCE_DIR)
    print("No files will be moved.")
    print("")

    found = 0

    try:
        with scandir(SOURCE_DIR) as entries:
            for entry in entries:
                if entry.is_file():
                    _, ext = splitext(entry.name)
                    if not ext:
                        continue

                    dest_dir = get_dest(ext)
                    print("Would move " + entry.name + " to " + dest_dir)
                    found += 1

    except Exception as e:
        print("Error scanning desktop.")
        print("Reason: " + str(e))
        return

    print("")
    print("Dry run complete.")
    print("Total files that would be moved: " + str(found))
    print("")