import os
import sys
import asyncio
import json
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, field_validator

# Add parent directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config
import helpers
import cleaner
import history
from watcher import watcher_manager
from logger import LOG_DIR


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_async(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    def broadcast_from_sync(self, message: dict):
        """Thread-safe sync wrapper to broadcast into the async loop."""
        try:
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_async(message), self._loop)
        except Exception as e:
            print("Broadcast error:", e)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    manager._loop = asyncio.get_running_loop()
    yield
    watcher_manager.stop_all()


app = FastAPI(title="File Organizer Dashboard", lifespan=lifespan)

# Add CORS security middleware
if config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

# Static and Template paths
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
helpers.ensure_dir(STATIC_DIR)
helpers.ensure_dir(TEMPLATES_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Pydantic Request Models with path validation
class ScanRequest(BaseModel):
    target_dir: str
    deep: bool = False
    quiet: bool = False

    @field_validator("target_dir")
    @classmethod
    def validate_path(cls, v: str) -> str:
        cleaned = os.path.abspath(v.strip())
        if not os.path.isdir(cleaned):
            raise ValueError("Directory does not exist: " + str(cleaned))
        return cleaned


class OrganizeRequest(BaseModel):
    target_dir: str
    deep: bool = False
    quiet: bool = False

    @field_validator("target_dir")
    @classmethod
    def validate_path(cls, v: str) -> str:
        cleaned = os.path.abspath(v.strip())
        if not os.path.isdir(cleaned):
            raise ValueError("Directory does not exist: " + str(cleaned))
        return cleaned


class WatcherRequest(BaseModel):
    target_dir: str
    deep: bool = False

    @field_validator("target_dir")
    @classmethod
    def validate_path(cls, v: str) -> str:
        cleaned = os.path.abspath(v.strip())
        if not os.path.isdir(cleaned):
            raise ValueError("Directory does not exist: " + str(cleaned))
        return cleaned


class CategoriesUpdateRequest(BaseModel):
    categories: Dict[str, List[str]]
    misc_category: Optional[str] = "Misc"


# WebSocket Endpoint with bidirectional commands
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to real-time File Organizer daemon"
        })
        while True:
            text_data = await websocket.receive_text()
            if text_data == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            try:
                msg = json.loads(text_data)
                action = msg.get("action")
                if action == "run":
                    target = os.path.abspath(msg.get("target_dir", "").strip())
                    mode = msg.get("mode", "dry_run")  # "clean", "dry_run", "summary"
                    deep = bool(msg.get("deep", False))

                    if not os.path.isdir(target):
                        await websocket.send_json({
                            "type": "error",
                            "error": "Invalid directory: " + str(target)
                        })
                        continue

                    def on_event(ev):
                        manager.broadcast_from_sync(ev)

                    scan_fn = cleaner.deep_scan_directory if deep else cleaner.process_directory
                    dry_run = mode != "clean"
                    quiet = mode == "summary"

                    await asyncio.to_thread(scan_fn, target, dry_run=dry_run, quiet=quiet, event_callback=on_event)

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# UI Routes & SEO
@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard template not found.</h1>"


@app.get("/faq", response_class=HTMLResponse)
async def get_faq():
    faq_path = os.path.join(TEMPLATES_DIR, "faq.html")
    if os.path.exists(faq_path):
        with open(faq_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>FAQ template not found.</h1>"


@app.get("/thank-you", response_class=HTMLResponse)
async def get_thank_you():
    thank_you_path = os.path.join(TEMPLATES_DIR, "thank_you.html")
    if os.path.exists(thank_you_path):
        with open(thank_you_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Thank you for using Tideway!</h1>"


@app.get("/robots.txt", response_class=PlainTextResponse)
async def get_robots():
    content = "User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /ws\n"
    return PlainTextResponse(content=content, media_type="text/plain")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        accept_header = request.headers.get("accept", "")
        # If API path or JSON requested without HTML
        if request.url.path.startswith("/api/") or ("application/json" in accept_header and "text/html" not in accept_header):
            return JSONResponse(status_code=404, content={"detail": exc.detail or "Not Found"})

        template_404 = os.path.join(TEMPLATES_DIR, "404.html")
        if os.path.exists(template_404):
            with open(template_404, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=404)
        return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(HTTPException)
async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        accept_header = request.headers.get("accept", "")
        if request.url.path.startswith("/api/") or ("application/json" in accept_header and "text/html" not in accept_header):
            return JSONResponse(status_code=404, content={"detail": exc.detail or "Not Found"})

        template_404 = os.path.join(TEMPLATES_DIR, "404.html")
        if os.path.exists(template_404):
            with open(template_404, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), status_code=404)
        return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# REST API Endpoints
@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "env": config.APP_ENV,
        "active_watchers": watcher_manager.list_active(),
        "total_runs": len(history.get_all_history())
    }


@app.get("/api/drives")
async def get_drives():
    return {
        "drives": helpers.get_available_drives(),
        "quick_locations": helpers.get_quick_locations()
    }


@app.get("/api/categories")
async def get_categories():
    config.reload_categories()
    return {
        "categories": config.CATEGORY_EXTENSIONS,
        "misc_category": config.MISC_CATEGORY,
        "order": config.CATEGORY_ORDER
    }


@app.post("/api/categories")
async def update_categories(req: CategoriesUpdateRequest):
    try:
        config.save_categories(req.categories, req.misc_category)
        return {
            "success": True,
            "message": "Categories updated successfully",
            "categories": config.CATEGORY_EXTENSIONS,
            "misc_category": config.MISC_CATEGORY
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/scan")
async def run_scan(req: ScanRequest):
    def on_event(event):
        manager.broadcast_from_sync(event)

    scan_fn = cleaner.deep_scan_directory if req.deep else cleaner.process_directory
    result = await asyncio.to_thread(scan_fn, req.target_dir, dry_run=True, quiet=req.quiet, event_callback=on_event)
    return result


@app.post("/api/organize")
async def run_organize(req: OrganizeRequest):
    def on_event(event):
        manager.broadcast_from_sync(event)

    scan_fn = cleaner.deep_scan_directory if req.deep else cleaner.process_directory
    result = await asyncio.to_thread(scan_fn, req.target_dir, dry_run=False, quiet=req.quiet, event_callback=on_event)
    return result


@app.get("/api/history")
async def get_history():
    return history.get_all_history()


@app.post("/api/history/{run_id}/undo")
async def undo_transaction(run_id: str):
    safe_run_id = os.path.basename(run_id)
    result = await asyncio.to_thread(history.undo_run, safe_run_id)
    if result["success"]:
        manager.broadcast_from_sync({
            "type": "undo_complete",
            "run_id": safe_run_id,
            "result": result
        })
    return result


@app.get("/api/watchers")
async def list_watchers():
    return watcher_manager.list_active()


@app.post("/api/watchers/start")
async def start_watcher(req: WatcherRequest):
    def on_event(event):
        manager.broadcast_from_sync(event)

    success, msg = watcher_manager.start(
        req.target_dir,
        deep=req.deep,
        event_callback=on_event
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    manager.broadcast_from_sync({
        "type": "watcher_status_changed",
        "action": "started",
        "path": req.target_dir,
        "deep": req.deep
    })
    return {"success": True, "message": msg, "watchers": watcher_manager.list_active()}


@app.post("/api/watchers/stop")
async def stop_watcher(req: WatcherRequest):
    success, msg = watcher_manager.stop(req.target_dir)
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    manager.broadcast_from_sync({
        "type": "watcher_status_changed",
        "action": "stopped",
        "path": req.target_dir
    })
    return {"success": True, "message": msg, "watchers": watcher_manager.list_active()}


@app.get("/api/logs")
async def list_logs():
    if not os.path.exists(LOG_DIR):
        return []
    logs = []
    for f in sorted(os.listdir(LOG_DIR), reverse=True):
        if f.endswith(".log"):
            p = os.path.join(LOG_DIR, f)
            logs.append({
                "filename": f,
                "path": p,
                "size": os.path.getsize(p),
                "modified": os.path.getmtime(p)
            })
    return logs


@app.get("/api/logs/{filename}")
async def get_log_content(filename: str):
    safe_name = os.path.basename(filename)
    log_file = os.path.join(LOG_DIR, safe_name)
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found")
    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        return {"filename": safe_name, "content": f.read()}


def run_server(host=None, port=None):
    import uvicorn
    server_host = host or config.APP_HOST
    server_port = port or config.APP_PORT
    uvicorn.run("dashboard.server:app", host=server_host, port=server_port, reload=False)


if __name__ == "__main__":
    run_server()
