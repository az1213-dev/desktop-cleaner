from os import scandir
from shutil import move 
from os.path import splitext, join 
from config import SOURCE_DIR, DEST_DIR_IMAGES, DEST_DIR_VIDEOS, DEST_DIR_AUDIO, DEST_DIR_DOCS, DEST_DIR_MISC 
from helpers import ensure_dir, make_unique, get_dest

def clean_desktop():
    print("Scanning " + SOURCE_DIR)

    files_moved = 0
    moved_imgs = 0
    moved_videos = 0 
    moved_audio = 0
    moved_docs = 0
    moved_misc = 0

    try:
        with scandir(SOURCE_DIR) as entries:
            for entry in entries:
                if entry.is_file():
                    _, ext = splitext(entry.name)
                    if not ext: continue

                    dest_dir = get_dest(ext)
                    ensure_dir(dest_dir)

                    unique_name = make_unique(dest_dir, entry.name)
                    dest_path = join(dest_dir, unique_name)

                    try:
                        print("Moving " + entry.name + " to " + dest_dir)
                        move(entry.path, dest_path)
                        files_moved += 1

                        if dest_dir == DEST_DIR_IMAGES:
                            moved_imgs += 1
                        elif dest_dir == DEST_DIR_VIDEOS:
                            moved_videos += 1
                        elif dest_dir == DEST_DIR_AUDIO:
                            moved_audio += 1
                        elif dest_dir == DEST_DIR_DOCS:
                            moved_docs += 1
                        else:
                            moved_misc += 1
                    
                    except Exception as e:
                        print("Error moving file: " + entry.name)
                        print("Reason: " + str(e))

    except Exception as e:
        print("Error scanning desktop")
        print("Reason: "+ str(e))
        return

    print("Cleaning complete.")
    print("Total files moved: " + str(files_moved))
    print("Images: " + str(moved_imgs))
    print("Videos: " + str(moved_videos))
    print("Audio: " + str(moved_audio))
    print("Documents: " + str(moved_docs))
    print("Misc: " + str(moved_misc))