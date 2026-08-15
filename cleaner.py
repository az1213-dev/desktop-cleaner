import os
from os import scandir
from os.path import splitext, join
from shutil import move

from config import CATEGORY_ORDER
from helpers import ensure_dir, make_unique, get_dest, get_category
from logger import start_log, write_log


def is_category_folder(name):
    """True if a folder name matches one of our own category folders
    (Images, Videos, Audio, Documents, Misc) - anywhere in the tree.
    Deep scan never descends into or removes these, since they're
    assumed to already be organized."""
    return name in CATEGORY_ORDER

def process_directory(source_dir, dry_run=False, quiet=False):
    """
    Scan source_dir and sort files into category subfolders.

    dry_run=True   -> report what would happen, move nothing.
    quiet=True     -> suppress per-file lines, only print the final summary.
                    (used for "Summary Only" menu options)

    Returns a dict of {category: count}.
    """
    mode = "Dry Run" if dry_run else "Cleaning"
    print(mode + ": Scanning " + source_dir)
    if dry_run:
        print("No files will be moved.")
    print("")

    counts = {category: 0 for category in CATEGORY_ORDER}

    log_path = None
    if not dry_run:
        log_path = start_log()
        write_log(log_path, "Target: " + source_dir)

    try:
        with scandir(source_dir) as entries:
            for entry in entries:
                if not entry.is_file():
                    continue

                _, ext = splitext(entry.name)
                if not ext:
                    continue

                category = get_category(ext)
                dest_dir = get_dest(ext, source_dir)

                if dry_run:
                    if not quiet:
                        print("Would move " + entry.name + " -> " + dest_dir)
                    counts[category] += 1
                    continue

                ensure_dir(dest_dir)
                unique_name = make_unique(dest_dir, entry.name)
                dest_path = join(dest_dir, unique_name)

                try:
                    if not quiet:
                        print("Moving " + entry.name + " -> " + dest_dir)
                    move(entry.path, dest_path)
                    counts[category] += 1
                    if log_path:
                        write_log(log_path, "MOVED: " + entry.path + " -> " + dest_path)
                except Exception as e:
                    print("Error moving file: " + entry.name)
                    print("Reason: " + str(e))
                    if log_path:
                        write_log(log_path, "ERROR: " + entry.name + " | " + str(e))

    except Exception as e:
        print("Error scanning " + source_dir)
        print("Reason: " + str(e))
        if log_path:
            write_log(log_path, "ERROR scanning " + source_dir + " | " + str(e))
        return counts

    print("")
    if dry_run:
        total = sum(counts.values())
        print("Dry run complete.")
        print("Total files that would be moved: " + str(total))
    else:
        total = sum(counts.values())
        print("Cleaning complete.")
        print("Total files moved: " + str(total))

    for category in CATEGORY_ORDER:
        print(category + ": " + str(counts[category]))
    print("")

    if log_path:
        write_log(log_path, "Total files moved: " + str(total))
        for category in CATEGORY_ORDER:
            write_log(log_path, category + ": " + str(counts[category]))
        print("Log saved to: " + log_path)
        print("")

    return counts


def summary_count(source_dir):
    """Report-only pass: same scan logic, no files moved, no per-file lines."""
    return process_directory(source_dir, dry_run=True, quiet=True)


def cleanup_empty_dirs(source_dir, log_path):
    """
    Walk source_dir bottom-up and remove any subfolder left empty,
    cascading upward (a parent that becomes empty because its last
    child was just removed gets removed too). Category folders and
    source_dir itself are never removed.

    Returns the list of removed folder paths, deepest first.
    """
    removed = []

    for dirpath, dirnames, filenames in os.walk(source_dir, topdown=False):
        if dirpath == source_dir:
            continue

        name = os.path.basename(dirpath)
        if is_category_folder(name):
            continue

        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                removed.append(dirpath)
                if log_path:
                    write_log(log_path, "REMOVED EMPTY FOLDER: " + dirpath)
        except Exception as e:
            print("Error removing folder: " + dirpath)
            print("Reason: " + str(e))

    return removed


def preview_empty_dirs(source_dir):
    """
    Dry-run equivalent of cleanup_empty_dirs: predicts which folders
    would end up empty (and therefore removed) once matching files are
    moved out, without touching the disk. A folder only "would be
    empty" if every file inside it has an extension (so it would move)
    and every subfolder inside it would also end up empty. Cascades
    upward the same way the real cleanup does.
    """
    would_remove = []
    removable = set()

    for dirpath, dirnames, filenames in os.walk(source_dir, topdown=False):
        if dirpath == source_dir:
            continue

        name = os.path.basename(dirpath)
        if is_category_folder(name):
            continue

        remaining_files = [f for f in filenames if not splitext(f)[1]]
        remaining_subdirs = [
            d for d in dirnames
            if is_category_folder(d) or join(dirpath, d) not in removable
        ]

        if not remaining_files and not remaining_subdirs:
            removable.add(dirpath)
            would_remove.append(dirpath)

    return would_remove


def deep_scan_directory(source_dir, dry_run=False, quiet=False):
    """
    Recursively scan every subfolder of source_dir and sort files into
    the top-level category folders (Images, Videos, etc.) - however
    deeply nested they are. Category folders are never descended into,
    anywhere in the tree, so already-organized files are left alone.

    After moving (real runs only), any subfolder left empty is removed,
    cascading upward until a non-empty folder is reached.

    dry_run=True   -> report what would happen, move and delete nothing.
    quiet=True     -> suppress per-file lines, only print the final summary.

    Returns a dict of {category: count}.
    """
    mode = "Dry Run (Deep Scan)" if dry_run else "Deep Scan"
    print(mode + ": Scanning " + source_dir)
    if dry_run:
        print("No files will be moved and no folders will be deleted.")
    print("")

    counts = {category: 0 for category in CATEGORY_ORDER}

    log_path = None
    if not dry_run:
        log_path = start_log()
        write_log(log_path, "Target: " + source_dir + " (deep scan)")

    try:
        for dirpath, dirnames, filenames in os.walk(source_dir, topdown=True):
            # Prune category folders from traversal so we never descend
            # into already-organized files, anywhere in the tree.
            dirnames[:] = [d for d in dirnames if not is_category_folder(d)]

            for filename in filenames:
                _, ext = splitext(filename)
                if not ext:
                    continue

                category = get_category(ext)
                dest_dir = get_dest(ext, source_dir)
                src_path = join(dirpath, filename)

                if dry_run:
                    if not quiet:
                        print("Would move " + src_path + " -> " + dest_dir)
                    counts[category] += 1
                    continue

                ensure_dir(dest_dir)
                unique_name = make_unique(dest_dir, filename)
                dest_path = join(dest_dir, unique_name)

                try:
                    if not quiet:
                        print("Moving " + src_path + " -> " + dest_dir)
                    move(src_path, dest_path)
                    counts[category] += 1
                    if log_path:
                        write_log(log_path, "MOVED: " + src_path + " -> " + dest_path)
                except Exception as e:
                    print("Error moving file: " + src_path)
                    print("Reason: " + str(e))
                    if log_path:
                        write_log(log_path, "ERROR: " + src_path + " | " + str(e))

    except Exception as e:
        print("Error scanning " + source_dir)
        print("Reason: " + str(e))
        if log_path:
            write_log(log_path, "ERROR scanning " + source_dir + " | " + str(e))
        return counts

    if dry_run:
        removed_dirs = preview_empty_dirs(source_dir)
    else:
        removed_dirs = cleanup_empty_dirs(source_dir, log_path)

    print("")
    total = sum(counts.values())
    if dry_run:
        print("Dry run complete.")
        print("Total files that would be moved: " + str(total))
    else:
        print("Deep scan complete.")
        print("Total files moved: " + str(total))

    for category in CATEGORY_ORDER:
        print(category + ": " + str(counts[category]))

    if removed_dirs:
        verb = "would be removed" if dry_run else "removed"
        print("")
        print("Empty folders " + verb + ": " + str(len(removed_dirs)))
        if not quiet:
            for folder in removed_dirs:
                print("  " + folder)
    print("")

    if log_path:
        write_log(log_path, "Total files moved: " + str(total))
        for category in CATEGORY_ORDER:
            write_log(log_path, category + ": " + str(counts[category]))
        print("Log saved to: " + log_path)
        print("")

    return counts