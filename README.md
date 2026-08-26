# 🌊 Tideway

A tidal force for your filesystem — sweep files into organized categories with live previews, auto-watchers, and instant rollback.

Built in Python with a modern **Real-Time Web Dashboard** (FastAPI + WebSockets + Tailwind CSS), **Background Auto-Organizer Daemon**, **One-Click Undo / Rollback**, and a rich **CLI interface**.

---

## 🚀 Key Features

- **🌐 Real-Time Web Dashboard** — A modern visual control center with live progress bars, dark mode, interactive Chart.js analytics, and move previews.
- **⚡ Live Activity Streaming** — Real-time event streaming via WebSockets (`[MOVED]`, `[DRY-RUN]`, `[REMOVED_FOLDER]`, `[WATCHDOG]`).
- **👀 Background Watcher Daemon** — Continuously monitors folders (like Downloads) using `watchdog` and auto-sorts files the moment they arrive.
- **↺ 1-Click Rollback / Undo** — Audit trail recorded for every operation as its own dedicated log file (`logs/run_*.log`), mapping out exact before & after file paths for instant reversal.
- **🔍 Dry Run & Diff Preview** — Inspect file lists, categories, and paths in a searchable table before touching any file.
- **📁 Standard vs. Deep Scan** — Choose between top-level sorting or full recursive tree scanning (with automated removal of empty subfolders).
- **🛡️ Collision-Safe Renaming** — Never overwrites existing files (`file_1.png`, `file_2.png`, etc.).
- **⚙️ Dynamic Rule Editor** — Modify extension mappings directly through the Web UI or `categories.json`.

### Supported Categories

**Images** · **Videos** · **Audio** · **Documents** · **Code & Web** · **Projects & Creative** · **Data & Databases** · **Archives** · **Executables** · **Fonts** · **Misc**

---

## 📂 Project Structure

```
tideway/
├── cleaner.py          # Core scanning, sorting, and event-driven moving engine
├── config.py           # Paths, category extension mappings, dynamic reloader
├── helpers.py          # Drive detection, unique naming, byte formatting, path helpers
├── history.py          # Log-based transaction parser & 1-click rollback engine
├── logger.py           # Timestamped run log files saved to logs/
├── main.py             # CLI interactive menu & command-line argument dispatcher
├── watcher.py          # Background watchdog daemon for live folder monitoring
├── requirements.txt    # Python dependencies
├── categories.json     # Extension-to-category mapping definitions
├── dashboard/
│   ├── server.py       # FastAPI backend with REST endpoints & WebSocket hub
│   ├── templates/
│   │   └── index.html  # Modern Tailwind CSS + Lucide Icons single-page UI
│   └── static/
│       └── app.js      # WebSocket controller, Chart.js graphs & UI interactions
└── tests/
    ├── test_organizer.py # Unit tests for cleaner, undo, and helpers
    └── test_api.py       # API and endpoint test suite
```

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/az1213-dev/file-organizer.git
   cd file-organizer
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   # Windows:
   .\.venv\Scripts\pip install -r requirements.txt
   # macOS/Linux:
   source .venv/bin/activate && pip install -r requirements.txt
   ```

---

## 🖥️ Running the Real-Time Web Dashboard

Launch the dashboard with a single command:

```bash
python main.py --dashboard
```
*Or specify a custom port:*
```bash
python main.py --dashboard --port 8080
```

Your default browser will open to `http://localhost:8000`.

### Dashboard Tabs:
- **Dashboard & Control:** Select quick locations (Downloads, Desktop, Drives), choose Standard vs. Deep Scan, and trigger Dry Runs or Live Organization.
- **Diff & Preview:** Search and filter files by category before executing changes.
- **Run History & Undo:** View past runs and rollback any operation.
- **Auto-Organizer Daemon:** Add and manage background folder watchers.
- **Categories & Rules:** Visual editor to add, remove, and modify category mappings.

---

## ⌨️ CLI Usage

You can also run the tool directly in your terminal:

```bash
python main.py
```

### Command-Line Flags:
```bash
# Launch Web Dashboard
python main.py --dashboard

# Run a Dry Run preview on Downloads (standard top-level)
python main.py --target "C:\Users\Username\Downloads" --dry-run

# Run a Deep Scan Clean on an entire drive
python main.py --target "D:\" --clean --deep

# Start background monitoring on Downloads
python main.py --watch "C:\Users\Username\Downloads"

# Undo the most recent run
python main.py --undo-last

# Undo a specific run ID
python main.py --undo "2026-08-24_20-35-12_abc123"
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.