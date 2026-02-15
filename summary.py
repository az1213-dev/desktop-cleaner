from config import *
from os.path import splitext
from helpers import get_dest
from os import scandir

def summary_count(source_dir):
    print("Summary: Scanning " + source_dir)
    print("No files will be moved.")
    print("")

    imgs = 0
    videos = 0
    audio = 0
    docs = 0
    misc = 0

    with scandir(source_dir) as entries:
        for entry in entries:
            if entry.is_file():
                _, ext = splitext(entry.name)
                if not ext: 
                    continue

                dest = get_dest(ext)
                
                # DOWNLOADS
                if source_dir == DOWNLOADS_DIR:
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

                # COUNT
                if dest == DEST_DIR_IMAGES or dest == DL_IMAGES:
                    imgs += 1
                elif dest == DEST_DIR_VIDEOS or dest == DL_VIDEOS:
                    videos += 1
                elif dest == DEST_DIR_AUDIO or dest == DL_AUDIO:
                    audio += 1
                elif dest == DEST_DIR_DOCS or dest == DL_DOCS:
                    docs += 1
                else:
                    misc += 1
    
    print("Summary: ")
    print("Images: " + str(imgs))
    print("Videos: " + str(videos))
    print("Audio: " + str(audio))
    print("Documents: " + str(docs))
    print("Misc: " + str(misc))
    print("")