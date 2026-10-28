from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pymupdf


def page_count(pdf_path: Path) -> int:
    doc = pymupdf.open(pdf_path)
    try:
        return doc.page_count
    finally:
        doc.close()


def metadata(pdf_path: Path) -> dict[str, Any]:
    doc = pymupdf.open(pdf_path)
    try:
        meta = doc.metadata or {}
        return {
            "title": (meta.get("title") or "").strip(),
            "author": (meta.get("author") or "").strip(),
            "page_count": doc.page_count,
        }
    finally:
        doc.close()


def extract_page(pdf_path: Path, index: int, session_dir: Path) -> dict[str, Any]:
    doc = pymupdf.open(pdf_path)
    try:
        if index < 0 or index >= doc.page_count:
            raise IndexError(f"page {index} out of range 0..{doc.page_count - 1}")
        page = doc[index]
        pages_dir = session_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        raster = pages_dir / f"{index:03d}.jpg"
        pix = page.get_pixmap(matrix=pymupdf.Matrix(1.7, 1.7), alpha=False)
        pix.save(str(raster), output="jpeg", jpg_quality=84)

        blocks = _text_blocks(page)
        plain = page.get_text("text") or ""
        tables = _tables(page) or _inferred_tables(page)
        images = _embedded_images(doc, page, pages_dir, index)

        return {
            "index": index,
            "page_count": doc.page_count,
            "width": float(page.rect.width),
            "height": float(page.rect.height),
            "plain": plain,
            "blocks": blocks,
            "tables": tables,
            "images": images,
            "raster": f"pages/{raster.name}",
        }
    finally:
        doc.close()


def _text_blocks(page) -> list[dict[str, Any]]:
    data = page.get_text("dict") or {}
    out: list[dict[str, Any]] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines_out = []
        max_size = 0.0
        texts = []
        for line in block.get("lines", []):
            spans = []
            for span in line.get("spans", []):
                text = (span.get("text") or "").strip()
                if not text:
                    continue
                size = float(span.get("size") or 0)
                max_size = max(max_size, size)
                spans.append({"text": text, "size": size, "font": span.get("font") or ""})
                texts.append(text)
            if spans:
                lines_out.append({"spans": spans, "text": " ".join(s["text"] for s in spans)})
        joined = " ".join(texts).strip()
        if not joined:
            continue
        out.append({"text": joined, "size": max_size, "lines": lines_out})
    return out


def _tables(page) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        finder = page.find_tables()
    except Exception:
        return out
    tables = getattr(finder, "tables", None) or []
    for table in tables:
        try:
            raw = table.extract() or []
        except Exception:
            continue
        rows = [[_clean_cell(c) for c in row] for row in raw if any(_clean_cell(c) for c in row)]
        if len(rows) < 2:
            continue
        headers = rows[0]
        body = rows[1:]
        if not any(headers) or not body:
            continue
        out.append({"headers": headers, "rows": body})
    return out


def _inferred_tables(page) -> list[dict[str, Any]]:
    words = page.get_text("words") or []
    if len(words) < 8:
        return []
    lines: dict[int, list[tuple[float, float, str]]] = {}
    for w in words:
        x0, y0, x1, _y1, text = float(w[0]), float(w[1]), float(w[2]), float(w[3]), str(w[4])
        key = int(round(y0 / 5.0) * 5)
        lines.setdefault(key, []).append((x0, x1, text))

    runs: list[list[list[str]]] = []
    current: list[list[str]] = []
    for y in sorted(lines):
        items = sorted(lines[y], key=lambda t: t[0])
        cells = _merge_cells(items)
        if _looks_tabular(items, cells):
            current.append(cells)
        else:
            if len(current) >= 3:
                runs.append(current)
            current = []
    if len(current) >= 3:
        runs.append(current)
    if not runs:
        return []
    rows = max(runs, key=len)
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows if len(r) >= 3]
    if len(rows) < 3:
        return []
    headers, body = rows[0], rows[1:]
    if not body:
        return []
    return [{"headers": headers, "rows": body}]


def _merge_cells(items: list[tuple[float, float, str]]) -> list[str]:
    if not items:
        return []
    cells = [[items[0][0], items[0][1], items[0][2]]]
    for x0, x1, text in items[1:]:
        prev = cells[-1]
        gap = x0 - prev[1]
        if gap < 16:
            prev[1] = x1
            prev[2] = (prev[2] + " " + text).strip()
        else:
            cells.append([x0, x1, text])
    return [c[2] for c in cells]


def _looks_tabular(items: list[tuple[float, float, str]], cells: list[str]) -> bool:
    if len(cells) < 3 or len(cells) > 8:
        return False
    xs = [it[0] for it in items]
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    wide = sum(1 for g in gaps if g > 36)
    packed = sum(1 for g in gaps if g < 14)
    if wide < 2:
        return False
    if packed > wide * 3:
        return False
    return True


def _clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _embedded_images(doc, page, pages_dir: Path, index: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[int] = set()
    for i, img in enumerate(page.get_images(full=True) or []):
        xref = int(img[0])
        if xref in seen:
            continue
        seen.add(xref)
        try:
            pix = pymupdf.Pixmap(doc, xref)
        except Exception:
            continue
        if pix.n >= 5:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        if pix.width < 48 or pix.height < 48:
            continue
        name = f"{index:03d}_img{i}.png"
        path = pages_dir / name
        try:
            pix.save(str(path))
        except Exception:
            continue
        out.append(
            {
                "file": f"pages/{name}",
                "width": pix.width,
                "height": pix.height,
            }
        )
    return out
