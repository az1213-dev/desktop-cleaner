import os
import sys
import shutil
import tempfile
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tideway import config
from tideway import helpers
from tideway import cleaner
from tideway import history


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

    # 3. Undo / Rollback Test
    run_id = clean_res["run_id"]
    assert run_id is not None
    undo_res = history.undo_run(run_id)
    assert undo_res["success"] is True
    assert undo_res["restored"] == 2
    # Verify files restored back to root temp_dir
    assert os.path.exists(img_file)
    assert os.path.exists(doc_file)


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


def test_log_file_history_and_no_json(temp_dir):
    test_file = os.path.join(temp_dir, "sample.png")
    with open(test_file, "w") as f:
        f.write("image")

    # Run clean
    res = cleaner.process_directory(temp_dir, dry_run=False)
    run_id = res["run_id"]
    log_path = res["log_path"]

    # Verify dedicated log file exists
    assert os.path.exists(log_path)
    assert log_path.endswith(".log")
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "MOVED:" in log_content
    assert "sample.png" in log_content

    # Verify history.json does NOT exist
    json_path = os.path.join(history.LOG_DIR, "history.json")
    assert not os.path.exists(json_path)

    # Verify history.get_all_history() reads from .log files
    all_runs = history.get_all_history()
    matching = [r for r in all_runs if r["run_id"] == run_id]
    assert len(matching) == 1
    assert matching[0]["total_files"] == 1

    # Verify undo updates log file
    undo_res = history.undo_run(run_id)
    assert undo_res["success"] is True
    with open(log_path, "r", encoding="utf-8") as f:
        updated_log = f.read()
    assert "UNDONE:" in updated_log


def test_validate_security_settings():
    # In development mode, insecure key should pass
    config.APP_ENV = "development"
    config.SECRET_KEY = "default-insecure-secret-key-please-change"
    config.validate_security_settings()

    # In production mode, insecure or empty key should raise RuntimeError
    config.APP_ENV = "production"
    config.SECRET_KEY = "default-insecure-secret-key-please-change"
    with pytest.raises(RuntimeError) as exc_info:
        config.validate_security_settings()
    assert "CRITICAL SECURITY ERROR" in str(exc_info.value)

    # In production mode with a proper 64-char key, it should pass
    config.SECRET_KEY = "1fb5864fbf871dd4a90650f4101ca33362999e0137c054bcacc864ccdf4ee9f1"
    config.validate_security_settings()

    # Reset back to development
    config.APP_ENV = "development"


def test_prune_old_logs(temp_dir):
    from tideway.logger import prune_old_logs, LOG_DIR
    # Test prune_old_logs does not crash with custom limit
    prune_old_logs(max_files=100)



