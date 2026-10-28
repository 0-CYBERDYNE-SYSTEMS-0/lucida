from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance


def paint_plate(chamber: dict[str, Any], session_dir: Path) -> str:
    pages = session_dir / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    index = int(chamber.get("index") or 0)
    path = pages / f"{index:03d}_plate.jpg"
    img = _render(chamber)
    img.save(path, "JPEG", quality=88, optimize=True)
    return f"pages/{path.name}"


def _render(chamber: dict[str, Any]) -> Image.Image:
    w, h = 1600, 900
    rng = random.Random(int(chamber.get("seed") or 1))
    kind = chamber.get("kind") or "narrative"
    palette = _palette(rng, kind)
    im = Image.new("RGB", (w, h), palette[0])

    # color washes
    for _ in range(rng.randint(4, 7)):
        col = palette[rng.randint(1, len(palette) - 1)]
        cx, cy = rng.randint(-100, w + 100), rng.randint(-80, h + 80)
        rw, rh = rng.randint(280, 820), rng.randint(180, 620)
        blob = Image.new("RGB", (w, h), palette[0])
        bd = ImageDraw.Draw(blob)
        bd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=col)
        blob = blob.filter(ImageFilter.GaussianBlur(radius=rng.randint(48, 90)))
        im = Image.blend(im, blob, rng.uniform(0.18, 0.38))

    d = ImageDraw.Draw(im)
    # star field
    for _ in range(900):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        b = rng.randint(90, 255)
        s = rng.choice((1, 1, 1, 2))
        d.ellipse([x, y, x + s, y + s], fill=(b, b - rng.randint(0, 30), b - rng.randint(0, 50)))

    cx, cy = w * 0.52, h * 0.46
    gold = palette[-1]
    ion = palette[2] if len(palette) > 2 else gold

    if kind in {"title", "narrative", "concept"}:
        _rings(d, rng, cx, cy, gold, ion)
        _nodes(d, rng, w, h, chamber.get("keywords") or [], ion, gold)
    elif kind == "data":
        _spectrogram(d, rng, w, h, gold, ion)
        _bars(d, rng, w, h, chamber.get("charts") or [], gold, ion)
        _rings(d, rng, w * 0.78, h * 0.32, gold, ion, count=4)
    elif kind == "formula":
        _rings(d, rng, cx, cy, gold, ion, count=10)
        _ticks(d, w, h, gold)
    elif kind == "figure":
        _reticle(d, cx, cy, gold)
        _rings(d, rng, cx, cy, gold, ion, count=5)
    else:
        _rings(d, rng, cx, cy, gold, ion)

    _reticle(d, cx, cy, gold)
    _vignette(im)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Color(im).enhance(0.92)
    _caption(im, chamber)
    return im


def _palette(rng: random.Random, kind: str) -> list[tuple[int, int, int]]:
    void = (8, 9, 14)
    if kind == "data":
        return [void, (18, 28, 32), (142, 236, 200), (212, 180, 90), (224, 122, 74)]
    if kind == "formula":
        return [void, (16, 18, 40), (180, 210, 255), (212, 180, 90), (90, 140, 220)]
    if kind == "figure":
        return [void, (28, 16, 14), (224, 122, 74), (212, 180, 90), (243, 234, 216)]
    return [void, (14, 16, 22), (212, 180, 90), (142, 236, 200), (243, 234, 216)]


def _rings(d: ImageDraw.ImageDraw, rng: random.Random, cx: float, cy: float, gold, ion, count: int = 7) -> None:
    for i in range(count):
        r = 40 + i * rng.randint(28, 54)
        col = gold if i % 2 == 0 else ion
        d.ellipse([cx - r, cy - r * 0.62, cx + r, cy + r * 0.62], outline=col, width=1)
        if rng.random() > 0.45:
            start = rng.uniform(0, 6.28)
            for a in [start + k * 0.04 for k in range(rng.randint(8, 28))]:
                x = cx + math.cos(a) * r
                y = cy + math.sin(a) * r * 0.62
                d.point((x, y), fill=col)


def _nodes(d, rng, w, h, keywords, ion, gold) -> None:
    pts = []
    for i, kw in enumerate(keywords[:10]):
        ang = (i / max(1, len(keywords[:10]))) * math.tau + rng.uniform(-0.2, 0.2)
        rad = rng.uniform(160, 340)
        x = w * 0.5 + math.cos(ang) * rad
        y = h * 0.48 + math.sin(ang) * rad * 0.55
        pts.append((x, y))
        r = 4 + min(14, float(kw.get("weight") or 1))
        d.ellipse([x - r, y - r, x + r, y + r], outline=ion, width=1)
    for i, a in enumerate(pts):
        for b in pts[i + 1 :]:
            if rng.random() > 0.62:
                d.line([a, b], fill=gold, width=1)


def _spectrogram(d, rng, w, h, gold, ion) -> None:
    y0 = int(h * 0.68)
    for x in range(80, w - 80, 6):
        ht = rng.randint(8, 90)
        col = ion if rng.random() > 0.55 else gold
        d.line([(x, y0), (x, y0 - ht)], fill=col, width=2)


def _bars(d, rng, w, h, charts, gold, ion) -> None:
    if not charts:
        return
    series = (charts[0].get("series") or [{}])[0]
    vals = [float(v) for v in (series.get("values") or [])][:12]
    if not vals:
        return
    mx = max(vals) or 1
    base_y = int(h * 0.78)
    gap = 46
    x0 = 120
    for i, v in enumerate(vals):
        bh = int((v / mx) * 220)
        x = x0 + i * gap
        d.rectangle([x, base_y - bh, x + 18, base_y], outline=gold if i % 2 == 0 else ion, width=1)


def _ticks(d, w, h, gold) -> None:
    y = int(h * 0.82)
    d.line([(80, y), (w - 80, y)], fill=gold, width=1)
    for i in range(33):
        x = 80 + i * ((w - 160) / 32)
        th = 18 if i % 8 == 0 else 8
        d.line([(x, y - th), (x, y + 2)], fill=gold, width=1)


def _reticle(d, cx, cy, gold) -> None:
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=gold, width=1)
    d.line([(cx - 46, cy), (cx - 22, cy)], fill=gold, width=1)
    d.line([(cx + 22, cy), (cx + 46, cy)], fill=gold, width=1)
    d.line([(cx, cy - 32), (cx, cy - 20)], fill=gold, width=1)
    d.line([(cx, cy + 20), (cx, cy + 32)], fill=gold, width=1)


def _vignette(im: Image.Image) -> None:
    w, h = im.size
    vig = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(vig)
    d.ellipse([-w * 0.05, -h * 0.15, w * 1.05, h * 1.12], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(radius=80))
    black = Image.new("RGB", (w, h), (4, 4, 6))
    im.paste(black, mask=ImageEnhance.Brightness(vig).enhance(0.55).point(lambda p: 255 - p))


def _caption(im: Image.Image, chamber: dict[str, Any]) -> None:
    font = _font(28)
    small = _font(16)
    d = ImageDraw.Draw(im)
    title = (chamber.get("title") or "")[:48]
    kind = (chamber.get("kind") or "").upper()
    idx = int(chamber.get("index") or 0) + 1
    d.text((64, 40), f"CH.{idx:02d}  ·  {kind}", font=small, fill=(212, 180, 90))
    d.text((64, 68), title, font=font, fill=(243, 234, 216))


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/BigCaslon.ttf",
        "/Library/Fonts/Georgia.ttf",
        "/System/Library/Fonts/NewYork.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()
