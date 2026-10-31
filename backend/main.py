"""
RepoRequiem - API.

Run locally:
    uvicorn main:app --reload --port 8000

Open http://localhost:5173 (dev) or http://localhost:8000 (built frontend).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from archaeology import (
    GitError,
    analyze,
    cleanup_clone,
    clone_public_repo,
    resolve_local_path,
)
from lore import answer_seance, engine_name, generate_lore

APP_VERSION = "1.0.0"
SCAN_TTL_SECONDS = int(os.getenv("SCAN_TTL_SECONDS", str(6 * 60 * 60)))
MAX_SCANS = int(os.getenv("MAX_SCANS", "16"))
ALLOW_LOCAL_PATHS = os.getenv("ALLOW_LOCAL_PATHS", "true").lower() not in {"0", "false", "no"}

app = FastAPI(title="RepoRequiem", version=APP_VERSION,
              description="Git archaeology with a local open-weight ghost.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanStore:
    def __init__(self) -> None:
        self._items: dict[str, dict] = {}
        self._lock = threading.Lock()

    def put(self, record: dict, clone_path: str | None) -> str:
        scan_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._evict()
            self._items[scan_id] = {
                "record": record,
                "lore": None,
                "created": time.time(),
                "clone_path": clone_path,
                "lore_lock": threading.Lock(),
            }
        return scan_id

    def get(self, scan_id: str) -> dict:
        with self._lock:
            item = self._items.get(scan_id)
            if not item:
                raise HTTPException(404, "That record has already been returned to the earth.")
            if time.time() - item["created"] > SCAN_TTL_SECONDS:
                self._drop(scan_id)
                raise HTTPException(410, "This record expired. Scan again.")
            return item

    def delete(self, scan_id: str) -> None:
        with self._lock:
            self._drop(scan_id)

    def _drop(self, scan_id: str) -> None:
        item = self._items.pop(scan_id, None)
        if item and item.get("clone_path"):
            cleanup_clone(item["clone_path"])

    def _evict(self) -> None:
        now = time.time()
        for scan_id, item in list(self._items.items()):
            if now - item["created"] > SCAN_TTL_SECONDS:
                self._drop(scan_id)
        while len(self._items) >= MAX_SCANS:
            oldest = min(self._items, key=lambda k: self._items[k]["created"])
            self._drop(oldest)

    def clear(self) -> None:
        with self._lock:
            for scan_id in list(self._items):
                self._drop(scan_id)


store = ScanStore()
scan_slots = threading.Semaphore(2)

BACKEND_DIR = Path(__file__).resolve().parent
DEMO_REPO = BACKEND_DIR / ".demo" / "lumen-mail"
DEMO_SCRIPT = BACKEND_DIR.parent / "scripts" / "make_demo_repo.py"
_demo_lock = threading.Lock()


def _build_demo() -> None:
    with _demo_lock:
        if DEMO_REPO.exists():
            return
        if not DEMO_SCRIPT.is_file():
            raise GitError("The demo repository is missing from this build.")
        DEMO_REPO.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT), str(DEMO_REPO)],
            capture_output=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise GitError("The demo repository could not be raised.")


def _looks_like_url(source: str) -> bool:
    if source.startswith(("http://", "https://")):
        return True
    if re.match(r"^(www\.)?(github|gitlab|bitbucket|codeberg)\.com/", source):
        return True
    return bool(re.fullmatch(r"[\w.-]+/[\w.-]+", source)) and not os.path.exists(source)


class ScanRequest(BaseModel):
    source: str = Field(min_length=1, max_length=400,
                        description="Absolute local path, or a public repository URL.")


class SeanceRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[dict] = Field(default_factory=list)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": APP_VERSION,
        "model": engine_name(),
        "local_paths": ALLOW_LOCAL_PATHS,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/scan")
async def scan(req: ScanRequest) -> dict:
    source = req.source.strip()
    if not source:
        raise HTTPException(400, "Give the archive a path or a repository URL.")

    if not scan_slots.acquire(blocking=False):
        raise HTTPException(429, "Two readings at a time. The candles are busy.")
    clone_path = None
    try:
        try:
            if _looks_like_url(source):
                repo_path, _ = await run_in_threadpool(clone_public_repo, source)
                clone_path = repo_path
            elif not ALLOW_LOCAL_PATHS:
                raise HTTPException(
                    400,
                    "This deployment only reads public repositories. "
                    "Run RepoRequiem locally to read a path on your own machine.",
                )
            else:
                repo_path = resolve_local_path(source)
            record = await run_in_threadpool(analyze, repo_path, int(os.getenv("MAX_COMMITS", "15000")))
        except GitError as exc:
            if clone_path:
                cleanup_clone(clone_path)
            raise HTTPException(400, str(exc)) from exc
        except HTTPException:
            if clone_path:
                cleanup_clone(clone_path)
            raise
        except Exception as exc:  # noqa: BLE001
            if clone_path:
                cleanup_clone(clone_path)
            raise HTTPException(500, f"The archive could not be read: {exc}") from exc

        scan_id = store.put(record, clone_path)
        return {"scan_id": scan_id, "record": record}
    finally:
        scan_slots.release()


@app.post("/api/demo")
async def demo() -> dict:
    """Raise the bundled haunted repository and read it. No path needed."""
    if not scan_slots.acquire(blocking=False):
        raise HTTPException(429, "Two readings at a time. The candles are busy.")
    try:
        try:
            await run_in_threadpool(_build_demo)
            record = await run_in_threadpool(analyze, str(DEMO_REPO), 1000)
        except GitError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(500, f"The demo could not be read: {exc}") from exc
        scan_id = store.put(record, None)
        return {"scan_id": scan_id, "record": record}
    finally:
        scan_slots.release()


@app.post("/api/scan/{scan_id}/haunt")
async def haunt(scan_id: str) -> dict:
    item = store.get(scan_id)
    if item["lore"]:
        return {"lore": item["lore"]}

    def _build() -> dict:
        with item["lore_lock"]:
            if item["lore"]:
                return item["lore"]
            item["lore"] = generate_lore(item["record"])
            return item["lore"]

    lore = await run_in_threadpool(_build)
    return {"lore": lore}


@app.post("/api/scan/{scan_id}/seance")
async def seance(scan_id: str, req: SeanceRequest) -> dict:
    item = store.get(scan_id)
    result = await run_in_threadpool(
        answer_seance, item["record"], req.question, req.history[-8:]
    )
    return result


@app.get("/api/scan/{scan_id}")
def get_scan(scan_id: str) -> dict:
    item = store.get(scan_id)
    return {"record": item["record"], "lore": item["lore"]}


@app.delete("/api/scan/{scan_id}")
def delete_scan(scan_id: str) -> dict:
    store.delete(scan_id)
    return {"ok": True}


@app.get("/api/scan/{scan_id}/export", response_class=PlainTextResponse)
def export_scan(scan_id: str) -> PlainTextResponse:
    item = store.get(scan_id)
    body = _markdown(item["record"], item["lore"])
    filename = f"{item['record']['meta']['name']}-requiem.md".replace(" ", "-")
    return PlainTextResponse(
        body,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.on_event("shutdown")
def _shutdown() -> None:
    store.clear()


def _markdown(record: dict, lore: dict | None) -> str:
    meta, life, totals = record["meta"], record["life"], record["totals"]
    out = [f"# {meta['name']} - a ghost record", ""]
    if lore:
        out += [f"> *{lore['epitaph']}*", "", lore["inscription"], ""]
        out += ["## The haunting", ""]
        for ch in lore["haunting"]:
            out += [f"### {ch['title']}", "", ch["text"], ""]
    out += [
        "## The record",
        "",
        f"- **Lifespan:** {str(life['first_commit'])[:10]} to {str(life['last_commit'])[:10]} "
        f"({life['lifespan_days']} days)",
        f"- **Commits:** {totals['commits']} across {totals['souls']} authors",
        f"- **Files:** {totals['files_live']} alive, {totals['files_vanished']} vanished",
        f"- **Lines:** +{totals['added']} / -{totals['deleted']}",
        f"- **Last words:** \"{life['last_words']}\" by {life['last_author']}",
        "",
        "## The buried",
        "",
        "| File | Lived | Died | Killed by | Last commit |",
        "| --- | --- | --- | --- | --- |",
    ]
    for g in record["ghosts"]:
        out.append(
            f"| `{g['path']}` | {str(g['born'])[:10]} | {str(g['died'])[:10]} | "
            f"{g['killed_by']} | {g['last_subject'][:60]} |"
        )
    if lore and lore.get("laments"):
        out += ["", "### What the files said", ""]
        for path, line in lore["laments"].items():
            out += [f"- **{path}** - {line}"]
    if record["forgotten"]:
        out += ["", "## The forgotten (alive, untouched)", ""]
        for f in record["forgotten"]:
            out.append(f"- `{f['path']}` - silent for {f['age_days']} days")
    if record["cursed"]:
        out += ["", "## Cursed commits", ""]
        for c in record["cursed"]:
            out.append(f"- **{c['title']}** - `{c['commit']}` {c['subject']} ({c['author']})")
    if record["extinct"]:
        out += ["", "## Extinct languages", ""]
        out += [f"- {e['language']} ({e['files_lost']} files lost)" for e in record["extinct"]]
    out += [
        "",
        "---",
        "",
        f"Read by RepoRequiem - git archaeology with a local open-weight ghost. "
        f"Voice: {lore['source']['model'] if lore and lore.get('source', {}).get('model') else 'the offline Archivist'}.",
    ]
    return "\n".join(out)


# --------------------------------------------------------------------------
# Production static frontend (optional)
# --------------------------------------------------------------------------
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.is_dir():
    assets = DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
