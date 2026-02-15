from os.path import splitext, exists, join 
from config import * 
import os

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path,exist_ok=True) 

def make_unique(dest_dir, name):
    filename, extension = splitext(name)
    count = 1
    new_name = name

    while exists(join(dest_dir,new_name)):
        new_name = filename + "_" + str(count) + extension
        count += 1
    
    return new_name

def get_dest(extension):
    ext = extension.lower()

    if ext in IMAGE_EXTENSIONS:
        return DEST_DIR_IMAGES
    if ext in VIDEO_EXTENSIONS:
        return DEST_DIR_VIDEOS
    if ext in AUDIO_EXTENSIONS:
        return DEST_DIR_AUDIO
    if ext in DOC_EXTENSIONS:
        return DEST_DIR_DOCS
    
    return DEST_DIR_MISC