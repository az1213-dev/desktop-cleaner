import os
import sys
import shutil
import tempfile
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from clutterctrl import config
from clutterctrl import helpers
from clutterctrl import cleaner
from clutterctrl import history


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="test_organizer_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_get_category():
    assert helpers.get_category(".png") == "Images"
    assert helpers.get_category(".mp4") == "Videos"
    assert helpers.get_category(".pdf") == "Documents"
    assert helpers.get_category(".unknownext123") == "Misc"


def test_format_bytes():
    assert helpers.format_bytes(500) == "500 B"
    assert "KB" in helpers.format_bytes(2048)
    assert "MB" in helpers.format_bytes(5 * 1024 * 1024)


def test_dry_run_and_clean_with_undo(temp_dir):
    # Create sample files
    img_file = os.path.join(temp_dir, "sample.png")
    doc_file = os.path.join(temp_dir, "report.pdf")
    with open(img_file, "w") as f:
        f.write("image data")
    with open(doc_file, "w") as f:
        f.write("document data")

    # 1. Dry Run Test
    events = []
    def on_event(ev):
        events.append(ev)

    dry_res = cleaner.process_directory(temp_dir, dry_run=True, event_callback=on_event)
    assert dry_res["total_files"] == 2
    assert dry_res["counts"]["Images"] == 1
    assert dry_res["counts"]["Documents"] == 1
    assert os.path.exists(img_file)
    assert os.path.exists(doc_file)
    assert len(events) > 0

    # 2. Real Clean Test
    clean_res = cleaner.process_directory(temp_dir, dry_run=False)
    assert clean_res["total_files"] == 2
    dest_img = os.path.join(temp_dir, "Images", "sample.png")
    dest_doc = os.path.join(temp_dir, "Documents", "report.pdf")
    assert os.path.exists(dest_img)
    assert os.path.exists(dest_doc)
    assert not os.path.exists(img_file)
    assert not os.path.exists(doc_file)

    # 3. Verify Unique Log File Exists
    run_id = clean_res["run_id"]
    assert run_id is not None
    log_path = history.get_log_path(run_id)
    assert os.path.isfile(log_path)
    assert log_path.endswith(".log")

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "MOVED:" in content
    assert "sample.png" in content
    assert "report.pdf" in content
    assert "Run ID:" in content

    # 4. Undo / Rollback Test
    undo_res = history.undo_run(run_id)
    assert undo_res["success"] is True
    assert undo_res["restored"] == 2
    # Verify files restored back to root temp_dir
    assert os.path.exists(img_file)
    assert os.path.exists(doc_file)

    # Verify log file is marked UNDONE
    with open(log_path, "r", encoding="utf-8") as f:
        undo_content = f.read()
    assert "UNDONE:" in undo_content or "STATUS: UNDONE" in undo_content


def test_deep_scan_and_cleanup_empty_dirs(temp_dir):
    nested_sub = os.path.join(temp_dir, "nested", "level2")
    os.makedirs(nested_sub, exist_ok=True)
    nested_file = os.path.join(nested_sub, "song.mp3")
    with open(nested_file, "w") as f:
        f.write("audio data")

    res = cleaner.deep_scan_directory(temp_dir, dry_run=False)
    assert res["counts"]["Audio"] == 1
    dest_audio = os.path.join(temp_dir, "Audio", "song.mp3")
    assert os.path.exists(dest_audio)
    # The empty nested directories should be removed
    assert not os.path.exists(nested_sub)


def test_unique_log_file_history_queries(temp_dir):
    test_file = os.path.join(temp_dir, "sample.png")
    with open(test_file, "w") as f:
        f.write("image")

    # Run clean
    res = cleaner.process_directory(temp_dir, dry_run=False)
    run_id = res["run_id"]

    # Verify history.get_all_history() reads from the unique log file
    all_runs = history.get_all_history()
    matching = [r for r in all_runs if r["run_id"] == run_id]
    assert len(matching) == 1
    assert matching[0]["total_files"] == 1

    # Verify undo updates log status
    undo_res = history.undo_run(run_id)
    assert undo_res["success"] is True
    undone_run = history.get_transaction(run_id)
    assert undone_run["undone"] is True
