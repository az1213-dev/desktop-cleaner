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


def test_api_watchers_start_and_stop(client, temp_test_dir):
    # Test starting watcher
    start_res = client.post("/api/watchers/start", json={"target_dir": temp_test_dir, "deep": False})
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["success"] is True
    assert len(start_data["watchers"]) >= 1

    # Test list watchers
    list_res = client.get("/api/watchers")
    assert list_res.status_code == 200
    watchers = list_res.json()
    assert any(os.path.normcase(w["path"]) == os.path.normcase(temp_test_dir) for w in watchers)

    # Test stopping watcher (using path with alternative slashes/casing)
    alt_path = temp_test_dir.replace("\\", "/")
    stop_res = client.post("/api/watchers/stop", json={"target_dir": alt_path})
    assert stop_res.status_code == 200
    stop_data = stop_res.json()
    assert stop_data["success"] is True
    assert not any(os.path.normcase(w["path"]) == os.path.normcase(temp_test_dir) for w in stop_data["watchers"])

    # Test stopping non-existent watcher returns 400 error string
    stop_again = client.post("/api/watchers/stop", json={"target_dir": temp_test_dir})
    assert stop_again.status_code == 400
    assert "Not currently watching" in stop_again.json()["detail"]


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


def test_history_api_for_csv_export(client, temp_test_dir):
    """Verify /api/history returns the expected fields that exportHistoryCSV() depends on."""
    # Create and organize files so history is populated
    f1 = os.path.join(temp_test_dir, "export_test.jpg")
    with open(f1, "w") as f:
        f.write("img")
    client.post("/api/organize", json={"target_dir": temp_test_dir, "deep": False})

    res = client.get("/api/history")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

    # Validate the schema that the CSV export function relies on
    if data:
        run = data[0]
        for field in ("run_id", "timestamp", "target_dir", "deep", "mode", "total_files", "undone", "moves"):
            assert field in run, f"Expected field '{field}' missing from /api/history entry"
        # Validate moves contain src and dest
        for move in run.get("moves", []):
            assert "src" in move and "dest" in move


def test_static_logo_and_index(client):
    index_res = client.get("/")
    assert index_res.status_code == 200
    assert "/static/logo.svg" in index_res.text

    logo_res = client.get("/static/logo.svg")
    assert logo_res.status_code == 200
    assert "<svg" in logo_res.text


def test_faq_page(client):
    res = client.get("/faq")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Frequently Asked Questions" in res.text
    assert "<title>Tideway — Frequently Asked Questions</title>" in res.text
    # Check internal links
    assert 'href="/"' in res.text
    assert 'href="/faq"' in res.text
    assert 'href="/thank-you"' in res.text
    assert 'href="/robots.txt"' in res.text
    # Check FAQ content sections
    assert "What is Tideway" in res.text
    assert "1-Click Rollback" in res.text
    assert "collision" in res.text.lower()


def test_thank_you_page(client):
    res = client.get("/thank-you")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Thank You" in res.text
    assert "<title>Tideway — Thank You</title>" in res.text
    # Check internal links
    assert 'href="/"' in res.text
    assert 'href="/faq"' in res.text
    assert 'href="/thank-you"' in res.text
    assert 'href="/robots.txt"' in res.text


def test_robots_txt(client):
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    assert "User-agent: *" in res.text
    assert "Allow: /" in res.text
    assert "Disallow: /api/" in res.text


def test_custom_404_html_page(client):
    res = client.get("/nonexistent-page-url")
    assert res.status_code == 404
    assert "text/html" in res.headers.get("content-type", "")
    assert "<title>Tideway — 404 Not Found</title>" in res.text
    assert "Lost at Sea?" in res.text
    assert 'href="/"' in res.text
    assert 'href="/faq"' in res.text
    assert 'href="/thank-you"' in res.text
    assert 'href="/robots.txt"' in res.text


def test_404_json_for_api(client):
    res = client.get("/api/nonexistent-endpoint")
    assert res.status_code == 404
    assert "application/json" in res.headers.get("content-type", "")
    data = res.json()
    assert "detail" in data


def test_unique_page_titles(client):
    index_res = client.get("/")
    faq_res = client.get("/faq")
    privacy_res = client.get("/privacy")
    terms_res = client.get("/terms")
    thank_you_res = client.get("/thank-you")
    not_found_res = client.get("/nonexistent-404")

    assert "<title>Tideway — Real-Time File Organizer &amp; Dashboard</title>" in index_res.text
    assert "<title>Tideway — Frequently Asked Questions</title>" in faq_res.text
    assert "<title>Tideway — Privacy Policy</title>" in privacy_res.text
    assert "<title>Tideway — Terms of Service</title>" in terms_res.text
    assert "<title>Tideway — Thank You</title>" in thank_you_res.text
    assert "<title>Tideway — 404 Not Found</title>" in not_found_res.text

    # Verify all 6 titles are distinct
    titles = [
        "Tideway — Real-Time File Organizer & Dashboard",
        "Tideway — Frequently Asked Questions",
        "Tideway — Privacy Policy",
        "Tideway — Terms of Service",
        "Tideway — Thank You",
        "Tideway — 404 Not Found"
    ]
    assert len(set(titles)) == 6


def test_privacy_page(client):
    res = client.get("/privacy")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Privacy Policy" in res.text
    assert "cookie-consent-banner" in res.text


def test_terms_page(client):
    res = client.get("/terms")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert "Terms of Service" in res.text
    assert "MIT" in res.text


def test_sitemap_xml(client):
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "xml" in res.headers.get("content-type", "")
    assert "<urlset" in res.text
    assert "<loc>/faq</loc>" in res.text
    assert "<loc>/privacy</loc>" in res.text


def test_manifest_json(client):
    res = client.get("/static/manifest.json")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Tideway — Real-Time File Organizer"
    assert data["display"] == "standalone"


def test_security_headers(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in res.headers.get("permissions-policy", "")




