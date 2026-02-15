# IMPORTS
from fileAutomation import (
    # Constants
    DOWNLOADS_DIR,
    DL_IMAGES, DL_AUDIO, DL_DOCS, DL_MISC, DL_VIDEOS,
    # Functions
    scandir, splitext, join, move, 
    ensure_dir, make_unique, get_dest
)

def clean_downloads():
    print("Scanning " + DOWNLOADS_DIR)

    files_moved = 0
    moved_imgs = 0
    moved_videos = 0
    moved_audio = 0
    moved_docs = 0
    moved_misc = 0

   
    with scandir(DOWNLOADS_DIR) as entries: 
        for entry in entries: 
            if entry.is_file():
                _, ext = splitext(entry.name)
                if not ext: 
                    continue 

                # Determine category of file
                dest_dir = get_dest(ext)
                
                # Map folders to downloads folders
                if dest_dir.endswith("Images"):
                    dest_dir = DL_IMAGES
                elif dest_dir.endswith("Videos"):
                    dest_dir = DL_VIDEOS
                elif dest_dir.endswith("Audio"):
                    dest_dir = DL_AUDIO
                elif dest_dir.endswith("Documents"):
                    dest_dir = DL_DOCS
                else: 
                    dest_dir = DL_MISC

                ensure_dir(dest_dir)

                unique_name = make_unique(dest_dir,entry.name)
                dest_path = join(dest_dir,unique_name)

                print("Moving " + entry.name + " to " + dest_dir)
                move(entry.path, dest_path)
                files_moved += 1

                if dest_dir == DL_IMAGES:
                    moved_imgs += 1
                elif dest_dir == DL_VIDEOS:
                    moved_videos += 1
                elif dest_dir == DL_AUDIO:
                    moved_audio += 1
                elif dest_dir == DL_DOCS:
                    moved_docs += 1
                else: 
                    moved_misc += 1

    print("Cleaning complete.")
    print("Total files moved: " + str(files_moved))
    print("Images: " + str(moved_imgs))
    print("Videos: " + str(moved_videos))
    print("Audio: " + str(moved_audio))
    print("Documents: " + str(moved_docs))
    print("Misc: " + str(moved_misc))