# file-organizer

A Python automation tool that keeps your files organized by automatically
sorting them into category folders — Images, Videos, Audio, Documents, and
Misc.

Originally built to clean up a single Desktop folder, it now works on
**any detected drive** as well as your Downloads folder, and supports a
dry run / summary mode so you can preview changes before anything moves.

## Features

- **Drive selection** — automatically detects available drives
  (`C:\`, `T:\`, `S:\`, etc. on Windows; mount points on macOS/Linux) and
  lets you choose which one to organize.
- **Downloads cleanup** — sorts your Downloads folder the same way.
- **Dry run mode** — preview exactly what would move, without touching
  any files.
- **Summary mode** — get file counts per category without a full
  file-by-file listing.
- **Safe by default** — only sorts files sitting directly in the chosen
  folder; it does not recurse into subfolders, so nested folders (like
  `Program Files` or `Windows` on a system drive) are left untouched.
- **No overwrites** — if a filename already exists at the destination,
  the tool automatically renames the incoming file (`photo_1.png`,
  `photo_2.png`, etc.) instead of overwriting anything.

## Project structure

| File          | Purpose                                                        |
|---------------|------------------------------------------------------------------|
| `config.py`   | Paths and the extension-to-category mapping                    |
| `helpers.py`  | Drive detection, directory creation, filename de-duplication   |
| `cleaner.py`  | Core scan/sort/move logic, shared by clean/dry-run/summary modes |
| `main.py`     | Interactive terminal menu / entry point                        |

## Usage

Run the tool from the project directory:

```bash
python main.py
```

You'll be prompted to choose a target:

```
File Automation Tool
--------------------
1. Organize a Drive
2. Organize Downloads
3. Exit
```

If you choose **Organize a Drive**, you'll see a list of detected drives
to pick from. Either way, you'll then choose a mode:

```
1. Clean (move files)
2. Dry Run (preview only, no files moved)
3. Summary Only (counts only, no files moved)
4. Back
```

## Categories

| Category  | Extensions                                                        |
|-----------|--------------------------------------------------------------------|
| Images    | `.jpg` `.jpeg` `.png` `.gif` `.webp` `.tiff` `.bmp` `.heic`       |
| Videos    | `.mp4` `.mov` `.avi` `.mkv` `.webm` `.flv`                        |
| Audio     | `.mp3` `.wav` `.aac` `.m4a` `.flac`                               |
| Documents | `.txt` `.pdf` `.doc` `.docx` `.ppt` `.pptx` `.xls` `.xlsx`        |
| Misc      | Anything else                                                     |

New extensions can be added by editing `CATEGORY_EXTENSIONS` in
`config.py` — no other code changes needed.

## Requirements

- Python 3.6+
- No external dependencies (standard library only)

## Notes

- Drive detection on Windows uses `GetLogicalDrives()` via `ctypes`; on
  macOS/Linux it falls back to `/` plus anything mounted under `/mnt` or
  `/Volumes`.
- Running **Clean** mode on a system drive (like `C:\`) will only affect
  loose files sitting at the root — it won't touch system folders — but
  it's still a good idea to run **Dry Run** first to see what would move.