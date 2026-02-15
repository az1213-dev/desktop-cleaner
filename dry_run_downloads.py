from config import *
from os import scandir
from os.path import splitext
from helpers import get_dest

def dry_run_downloads():
    print("Dry Run (Downloads): Scanning" + DOWNLOADS_DIR)
    print("No files will be moved")
    print("")

    found = 0

    try:
        with scandir(DOWNLOADS_DIR) as entries:
            for entry in entries:
                if entry.is_file():
                    _, ext = splitext(entry.name)
                    if not ext: 
                        continue

                    dest = get_dest(ext)

                    # Map Desktop to Downloads
                    if dest == DEST_DIR_IMAGES:
                        dest = DL_IMAGES
                    elif dest == DEST_DIR_VIDEOS:
                        dest = DL_VIDEOS
                    elif dest == DEST_DIR_AUDIO:
                        dest = DL_AUDIO
                    elif dest == DEST_DIR_DOCS:
                        dest = DL_DOCS
                    else: 
                        dest = DL_MISC
    
                    print("Would move " + entry.name + " to " + dest)
                    found += 1

    except Exception as e:
                print("Error scanning downloads.")
                print("Reason: " + str(e))
                return 

    print("")
    print("Dry run complete.")
    print("Total files that would be moved: " + str(found))
    print("")