import os
import sys
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dashboard.server import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_test_dir():
    d = tempfile.mkdtemp(prefix="test_api_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_api_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] == "online"


def test_api_drives(client):
    res = client.get("/api/drives")
    assert res.status_code == 200
    data = res.json()
    assert "drives" in data
    assert "quick_locations" in data


def test_api_categories(client):
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "Images" in data["categories"]


def test_api_scan_and_organize(client, temp_test_dir):
    # Create test files
    f1 = os.path.join(temp_test_dir, "test1.jpg")
    f2 = os.path.join(temp_test_dir, "test2.pdf")
    with open(f1, "w") as f:
        f.write("image")
    with open(f2, "w") as f:
        f.write("pdf")

    # Test /api/scan (Dry Run)
    scan_res = client.post("/api/scan", json={"target_dir": temp_test_dir, "deep": False})
    assert scan_res.status_code == 200
    scan_data = scan_res.json()
    assert scan_data["total_files"] == 2
    assert scan_data["dry_run"] is True
    assert os.path.exists(f1)
    assert os.path.exists(f2)

    # Test /api/organize (Real Clean)
    org_res = client.post("/api/organize", json={"target_dir": temp_test_dir, "deep": False})
    assert org_res.status_code == 200
    org_data = org_res.json()
    assert org_data["total_files"] == 2
    assert org_data["dry_run"] is False
    dest_jpg = os.path.join(temp_test_dir, "Images", "test1.jpg")
    dest_pdf = os.path.join(temp_test_dir, "Documents", "test2.pdf")
    assert os.path.exists(dest_jpg)
    assert os.path.exists(dest_pdf)

    # Test /api/history and /api/history/{run_id}/undo
    run_id = org_data["run_id"]
    undo_res = client.post("/api/history/" + str(run_id) + "/undo")
    assert undo_res.status_code == 200
    undo_data = undo_res.json()
    assert undo_data["success"] is True
    assert os.path.exists(f1)
    assert os.path.exists(f2)

