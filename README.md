# 🌊 Tideway

A tidal force for your filesystem — sweep files into organized categories with live previews, auto-watchers, and instant rollback.

Built in Python with a modern **Real-Time Web Dashboard** (FastAPI + WebSockets + Tailwind CSS), **Background Auto-Organizer Daemon**, **One-Click Undo / Rollback**, and a rich **CLI interface**.

---

## 🚀 Key Features

- **🌐 Real-Time Web Dashboard** — A modern visual control center with live progress bars, dark mode, interactive Chart.js analytics, and move previews.
- **⚡ Live Activity Streaming** — Real-time event streaming via WebSockets (`[MOVED]`, `[DRY-RUN]`, `[REMOVED_FOLDER]`, `[WATCHDOG]`).
- **👀 Background Watcher Daemon** — Continuously monitors folders (like Downloads) using `watchdog` and auto-sorts files the moment they arrive.
- **↺ 1-Click Rollback / Undo** — Audit trail recorded for every operation as its own dedicated log file (`tideway/logs/run_*.log`), mapping out exact before & after file paths for instant reversal.
- **📊 CSV Export** — Export complete run histories and transaction logs directly to CSV from the dashboard.
- **🔍 Dry Run & Diff Preview** — Inspect file lists, categories, and paths in a searchable table before touching any file.
- **📁 Standard vs. Deep Scan** — Choose between top-level sorting or full recursive tree scanning (with automated removal of empty subfolders).
- **🛡️ Collision-Safe Renaming** — Never overwrites existing files (`file_1.png`, `file_2.png`, etc.).
- **⚙️ Dynamic Rule Editor** — Modify extension mappings directly through the Web UI or `categories.json`.
- **📄 Built-in Pages & SEO** — Dedicated FAQ page (`/faq`), Privacy Policy (`/privacy`), Terms of Service (`/terms`), Thank You page (`/thank-you`), `sitemap.xml`, `robots.txt`, Web App Manifest, and customized HTML/JSON 404 error handlers.

### Supported Categories

**Images** · **Videos** · **Audio** · **Documents** · **Code & Web** · **Projects & Creative** · **Data & Databases** · **Archives** · **Executables** · **Fonts** · **Misc**

---

## 📂 Project Structure

```
tideway/
├── tideway/                    # Core Tideway Python package
│   ├── __init__.py             # Package marker and module overview
│   ├── cleaner.py              # Core scanning, sorting, and event-driven moving engine
│   ├── config.py               # Paths, category extension mappings, dynamic reloader, .env
│   ├── helpers.py              # Drive detection, unique naming, byte formatting, path helpers
│   ├── history.py              # Log-based transaction parser & 1-click rollback engine
│   ├── logger.py               # Timestamped run log files saved to logs/
│   ├── main.py                 # CLI interactive menu & command-line argument dispatcher
│   ├── watcher.py              # Background watchdog daemon for live folder monitoring
│   ├── categories.json         # Extension-to-category mapping definitions
│   └── logs/                   # Audit trail logs (run_*.log)
├── dashboard/                  # Web dashboard application
│   ├── server.py               # FastAPI backend with REST endpoints & WebSocket hub
│   ├── templates/              # HTML templates
│   │   ├── index.html          # Modern Tailwind CSS + Lucide Icons single-page UI
│   │   ├── faq.html            # Frequently Asked Questions page
│   │   ├── privacy.html        # Privacy Policy & data disclosure page
│   │   ├── terms.html          # Terms of Service & MIT software license
│   │   ├── thank_you.html      # Thank You page
│   │   └── 404.html            # Custom styled 404 error page
│   └── static/                 # Static assets
│       ├── app.js              # WebSocket controller, Chart.js graphs & UI interactions
│       ├── manifest.json       # Web App Manifest for PWA & mobile bookmarking
│       └── logo.svg            # Application vector logo
├── tests/                      # Automated test suite
│   ├── __init__.py
│   ├── test_organizer.py       # Unit tests for cleaner, undo, and helpers
│   └── test_api.py             # API, WebSockets, static routes, and endpoint test suite
├── .env.example                # Example environment configuration
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Runtime dependencies
└── requirements-dev.txt        # Development and testing dependencies
```

---

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/az1213-dev/tideway.git
   cd tideway
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python -m venv .venv

   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt -r requirements-dev.txt

   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. **(Optional) Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

---

## 🖥️ Running the Real-Time Web Dashboard

Launch the dashboard with:

```bash
python -m tideway.main --dashboard
```

*Or specify a custom port:*
```bash
python -m tideway.main --dashboard --port 8080
```

Your default browser will open automatically to `http://localhost:8000`.

### Dashboard Tabs & Pages:
- **Dashboard & Control:** Select quick locations (Downloads, Desktop, Drives), choose Standard vs. Deep Scan, and trigger Dry Runs or Live Organization.
- **Diff & Preview:** Search and filter files by category before executing changes.
- **Run History & Undo:** View past runs, export transaction logs as CSV, and rollback any operation.
- **Auto-Organizer Daemon:** Add and manage background folder watchers.
- **Categories & Rules:** Visual editor to add, remove, and modify category mappings.
- **Informational Pages:** Built-in `/faq`, `/thank-you`, and `/robots.txt`.

---

## ⌨️ CLI Usage

You can also run Tideway directly in your terminal:

```bash
python -m tideway.main
```

### Command-Line Options:
```bash
# Launch Web Dashboard
python -m tideway.main --dashboard

# Run a Dry Run preview on Downloads (standard top-level)
python -m tideway.main --target "C:\Users\Username\Downloads" --dry-run

# Run a Deep Scan Clean on an entire directory or drive
python -m tideway.main --target "D:\" --clean --deep

# Start background monitoring on Downloads
python -m tideway.main --watch "C:\Users\Username\Downloads"

# Start background monitoring with recursive deep scanning
python -m tideway.main --watch "C:\Users\Username\Downloads" --deep

# Undo the most recent run
python -m tideway.main --undo-last

# Undo a specific run ID
python -m tideway.main --undo "run_2026-08-26_20-45-25_3555e1"
```

---

## 🧪 Running Tests

Run the test suite with `pytest`:

```bash
pytest
```

To run with verbose output:
```bash
pytest -v
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.