"""
Tideway
~~~~~~~

A tidal force for your filesystem — sweeps files into organized
categories with live previews, auto-watchers, and instant rollback.

Modules:
    config   - environment settings, paths, and category definitions
    helpers  - filesystem utilities (drive detection, byte formatting, categorization)
    cleaner  - core file-organizing logic (standard + deep scans)
    watcher  - background folder watcher using watchdog
    history  - transaction logging, undo/rollback support
    logger   - low-level log file read/write helpers
    main     - CLI entry point and interactive menu
"""