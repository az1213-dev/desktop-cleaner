from os import scandir
from os.path import splitext, join
from shutil import move

from config import CATEGORY_ORDER
from helpers import ensure_dir, make_unique, get_dest, get_category


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
                except Exception as e:
                    print("Error moving file: " + entry.name)
                    print("Reason: " + str(e))

    except Exception as e:
        print("Error scanning " + source_dir)
        print("Reason: " + str(e))
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

    return counts


def summary_count(source_dir):
    """Report-only pass: same scan logic, no files moved, no per-file lines."""
    return process_directory(source_dir, dry_run=True, quiet=True)