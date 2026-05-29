from __future__ import annotations

import json
import os
from collections import deque
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from shmlrp.config import load_config
from shmlrp.orchestration.pipeline import run_pipeline

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="Self-Healing ML Reliability Platform")
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
config = load_config()

_allow_all_cors = os.getenv("SHMLRP_ALLOW_ALL_CORS", "").lower() in {"1", "true", "yes"}
_origins_env = os.getenv("SHMLRP_ALLOWED_ORIGINS", "")
_allowed_origins = [origin.strip() for origin in _origins_env.split(",") if origin.strip()]

if _allow_all_cors or _allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if _allow_all_cors else _allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class RunRequest(BaseModel):
    drift_probability: float | None = None
    sample_size: int | None = None
    seed: int | None = None


@app.on_event("startup")
def _startup() -> None:
    app.state.latest_report = None


@app.get("/")
def root() -> dict:
    return {
        "service": "Self-Healing ML Reliability Platform",
        "status": "ok",
        "ui": "/ui",
        "docs": "/docs",
        "health": "/health",
        "run": "/run",
        "latest": "/latest",
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    icon_path = WEB_DIR / "favicon.svg"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/svg+xml")
    return Response(status_code=204)


@app.get("/styles.css", include_in_schema=False)
def styles() -> Response:
    css_path = WEB_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return Response(status_code=404)


@app.get("/app.js", include_in_schema=False)
def app_js() -> Response:
    js_path = WEB_DIR / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return Response(status_code=404)


@app.get("/config.js", include_in_schema=False)
def config_js() -> Response:
    config_path = WEB_DIR / "config.js"
    if config_path.exists():
        return FileResponse(config_path, media_type="application/javascript")
    return Response(status_code=404)


@app.get("/favicon.svg", include_in_schema=False)
def favicon_svg() -> Response:
    icon_path = WEB_DIR / "favicon.svg"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/svg+xml")
    return Response(status_code=404)


@app.get("/ui", include_in_schema=False)
def ui() -> HTMLResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("UI assets missing", status_code=500)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


def _read_recent_jsonl(path: Path, limit: int) -> list[dict]:
    limit = max(1, min(limit, 200))
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        lines = deque((line.strip() for line in handle if line.strip()), maxlen=limit)
    return [json.loads(line) for line in lines]


@app.get("/metrics/recent")
def metrics_recent(limit: int = 20) -> list[dict]:
    metrics_path = config.artifacts_dir / "metrics.jsonl"
    return _read_recent_jsonl(metrics_path, limit)


@app.post("/run")
def run(request: RunRequest) -> dict:
    report = run_pipeline(
        config,
        drift_probability=request.drift_probability,
        sample_size=request.sample_size,
        seed=request.seed,
    )
    app.state.latest_report = report
    return report


@app.get("/latest")
def latest() -> dict:
    return app.state.latest_report or {}
