#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lucida.analyze import analyze  # noqa: E402
from lucida.art import paint_plate  # noqa: E402
from lucida.extract import extract_page, metadata, page_count  # noqa: E402
from lucida.sample_book import ensure_sample  # noqa: E402

DATA = ROOT / "data"
STATIC = ROOT / "static"
SAMPLE = DATA / "sample" / "starforge.pdf"
MAX_UPLOAD = 80 * 1024 * 1024

_locks: dict[str, Lock] = {}
_meta_lock = Lock()


def _lock(key: str) -> Lock:
    with _meta_lock:
        return _locks.setdefault(key, Lock())


app = FastAPI(title="LUCIDA", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "name": "lucida"}


def _new_session(pdf_bytes: bytes, filename: str, demo: bool = False) -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    sid = uuid.uuid4().hex[:12]
    dest = DATA / sid
    dest.mkdir(parents=True, exist_ok=True)
    pdf = dest / "book.pdf"
    pdf.write_bytes(pdf_bytes)
    meta = metadata(pdf)
    title = meta.get("title") or Path(filename).stem
    session = {
        "id": sid,
        "title": title,
        "author": meta.get("author") or "",
        "page_count": page_count(pdf),
        "filename": filename,
        "demo": demo,
    }
    (dest / "session.json").write_text(json.dumps(session, indent=2), encoding="utf-8")
    return session


@app.post("/api/demo")
def open_demo() -> dict[str, Any]:
    src = ensure_sample(SAMPLE)
    return _new_session(src.read_bytes(), "starforge.pdf", demo=True)


@app.post("/api/open")
async def open_book(file: UploadFile = File(...)) -> dict[str, Any]:
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "drop a PDF, or open the sample atlas")
    blob = await file.read()
    if not blob:
        raise HTTPException(400, "empty file")
    if len(blob) > MAX_UPLOAD:
        raise HTTPException(400, "PDF larger than 80 MB")
    return _new_session(blob, Path(file.filename or "book.pdf").name, demo=False)


@app.get("/api/session/{sid}")
def get_session(sid: str) -> dict[str, Any]:
    path = DATA / sid / "session.json"
    if not path.exists():
        raise HTTPException(404, "session gone")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/session/{sid}/page/{index}")
def get_page(sid: str, index: int) -> dict[str, Any]:
    dest = DATA / sid
    pdf = dest / "book.pdf"
    if not pdf.exists():
        raise HTTPException(404, "session gone")
    count = page_count(pdf)
    if index < 0 or index >= count:
        raise HTTPException(404, "no such page")
    cache = dest / "pages" / f"{index:03d}.json"
    with _lock(f"{sid}:{index}"):
        if cache.exists():
            chamber = json.loads(cache.read_text(encoding="utf-8"))
        else:
            raw = extract_page(pdf, index, dest)
            chamber = analyze(raw)
            chamber["plate"] = paint_plate(chamber, dest)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(chamber, indent=2), encoding="utf-8")
    chamber = dict(chamber)
    chamber["media_base"] = f"/media/{sid}"
    return chamber


@app.get("/media/{sid}/{rest:path}")
def media(sid: str, rest: str) -> FileResponse:
    path = (DATA / sid / rest).resolve()
    root = (DATA / sid).resolve()
    if root not in path.parents and path != root:
        raise HTTPException(400, "bad path")
    if not path.is_file():
        raise HTTPException(404, "missing")
    return FileResponse(path)


app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    DATA.mkdir(parents=True, exist_ok=True)
    ensure_sample(SAMPLE)
    print("LUCIDA  →  http://127.0.0.1:7474")
    uvicorn.run(app, host="127.0.0.1", port=7474, log_level="info")
