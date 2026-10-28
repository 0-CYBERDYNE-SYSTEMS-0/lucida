from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any


STOP = {
    "the", "a", "an", "of", "to", "and", "in", "is", "it", "for", "on", "with",
    "as", "by", "from", "that", "this", "are", "was", "be", "or", "at", "we",
    "you", "they", "their", "its", "into", "than", "then", "which", "not",
    "but", "have", "has", "had", "were", "been", "will", "can", "may", "each",
    "also", "more", "most", "such", "these", "those", "over", "after", "before",
    "between", "through", "about", "when", "where", "what", "who", "how",
    "page", "figure", "table", "chapter", "volume", "see", "used", "using",
    "one", "two", "three", "four", "five", "our", "your", "all", "any", "both",
    "other", "some", "only", "same", "own", "just", "very", "there", "here",
    "does", "did", "doing", "done", "being", "because", "while", "during",
}

KIND_TITLE = "title"
KIND_DATA = "data"
KIND_CONCEPT = "concept"
KIND_FIGURE = "figure"
KIND_NARRATIVE = "narrative"
KIND_FORMULA = "formula"


def analyze(raw: dict[str, Any]) -> dict[str, Any]:
    plain = raw.get("plain") or ""
    blocks = raw.get("blocks") or []
    tables = raw.get("tables") or []
    images = raw.get("images") or []
    index = int(raw.get("index") or 0)
    page_count = int(raw.get("page_count") or 1)

    title = _title(blocks, plain, index)
    lede, body = _lede_body(blocks, title)
    quotes = _quotes(plain)
    keywords = _keywords(plain, title)
    stats = _stats(plain, tables)
    charts = _charts(tables)
    kind = _kind(index, plain, blocks, tables, images, stats, charts)
    idea, question, answer = _lesson(title, lede, quotes, tables, stats, kind)
    seed = int(hashlib.sha256(f"{index}|{title}|{plain[:800]}".encode("utf-8")).hexdigest()[:12], 16)
    prompt = _prompt(kind, title, keywords, lede)

    return {
        "index": index,
        "page_count": page_count,
        "kind": kind,
        "title": title,
        "lede": lede,
        "idea": idea,
        "question": question,
        "answer": answer,
        "body": body[:8],
        "quotes": quotes[:3],
        "keywords": keywords[:14],
        "stats": stats[:6],
        "tables": tables[:3],
        "charts": charts[:3],
        "images": images[:6],
        "raster": raw.get("raster"),
        "seed": seed,
        "prompt": prompt,
        "reading_seconds": max(20, min(180, len(plain.split()) * 60 // 180 or 20)),
        "word_count": len(plain.split()),
    }


def _title(blocks: list[dict[str, Any]], plain: str, index: int) -> str:
    sized = [(float(b.get("size") or 0), (b.get("text") or "").strip()) for b in blocks]
    sized = [(s, t) for s, t in sized if t and 2 <= len(t) <= 90]
    if sized:
        sized.sort(key=lambda x: (-x[0], len(x[1])))
        top_size = sized[0][0]
        headings = [t for s, t in sized if s >= top_size * 0.86]
        # prefer a short display line
        headings.sort(key=lambda t: (0 if 8 <= len(t) <= 48 else 1, -len(t) if len(t) < 18 else len(t)))
        return _tidy(headings[0])
    line = next((ln.strip() for ln in plain.splitlines() if ln.strip()), "")
    return _tidy(line) if line else f"Chamber {index + 1:02d}"


def _lede_body(blocks: list[dict[str, Any]], title: str) -> tuple[str, list[str]]:
    paras: list[str] = []
    for b in blocks:
        t = _tidy(b.get("text") or "")
        if not t or t.lower() == title.lower():
            continue
        if len(t) < 28:
            continue
        if t in paras:
            continue
        paras.append(t)
    lede = paras[0] if paras else ""
    body = paras[1:] if len(paras) > 1 else []
    if not body and lede and len(lede) > 220:
        parts = re.split(r"(?<=[.!?])\s+", lede)
        if len(parts) > 2:
            lede = " ".join(parts[:2])
            body = [" ".join(parts[2:])]
    return lede, body


def _quotes(plain: str) -> list[str]:
    found = re.findall(r"[“\"]([^”\"]{20,180})[”\"]", plain)
    return [_tidy(q) for q in found]


def _keywords(plain: str, title: str) -> list[dict[str, Any]]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", plain)
    freq: Counter[str] = Counter()
    caps: Counter[str] = Counter()
    for w in words:
        low = w.lower()
        if low in STOP or not re.search(r"[aeiou]", low):
            continue
        freq[low] += 1
        if w[:1].isupper():
            caps[low] += 1
    for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", title):
        low = w.lower()
        if low not in STOP:
            freq[low] += 3
    ranked = []
    for word, n in freq.most_common(40):
        score = n + caps[word] * 1.4 + (2 if "-" in word else 0)
        ranked.append({"word": word, "weight": round(score, 2)})
    ranked.sort(key=lambda x: -x["weight"])
    return ranked


_FRAG = re.compile(
    r"\b(about|than|happens|colliding|tense|every|most|same|rest|detected|cooler|under|written)\b",
    re.I,
)


def _good_label(label: str) -> bool:
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-/]*", label or "")
    if not (1 <= len(words) <= 8):
        return False
    if _FRAG.search(label or ""):
        return False
    return True


def _stats(plain: str, tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(label: str, value: str) -> None:
        label = _tidy(label)
        value = _tidy(value)
        if not label or not value or len(label) < 3:
            return
        if not _good_label(label):
            return
        key = f"{label}|{value}".lower()
        if key in seen:
            return
        seen.add(key)
        out.append({"label": label[:42], "value": value[:28]})

    for table in tables[:1]:
        headers = table.get("headers") or []
        rows = table.get("rows") or []
        scored: list[tuple[float, list[tuple[float, str, str]]]] = []
        for ci, h in enumerate(headers):
            if ci == 0 or re.search(r"note|fate|color|example", str(h), re.I):
                continue
            pairs = []
            for row in rows:
                name = (row[0] if row else "") or ""
                num = _to_float(row[ci] if ci < len(row) else "")
                if num is None or not name:
                    continue
                pairs.append((num, name, str(h)))
            pos = [p[0] for p in pairs if p[0] > 0]
            if len(pairs) < 2 or len(pos) < 2:
                continue
            span = max(pos) / min(pos) if min(pos) else 1
            scored.append((span, pairs))
        scored.sort(key=lambda t: -t[0])
        for _span, pairs in scored[:2]:
            hi = max(pairs, key=lambda t: t[0])
            lo = min(pairs, key=lambda t: t[0])
            add(f"{hi[1]} · {hi[2]}", _fmt(hi[0]))
            add(f"{lo[1]} · {lo[2]}", _fmt(lo[0]))

    pair = re.compile(
        r"^([A-Za-z][A-Za-z0-9/ \-]{3,40}?)\s{2,}(\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?(?:\s*[A-Za-z/%²³³]+)*)$",
        re.M,
    )
    for m in pair.finditer(plain):
        add(m.group(1), m.group(2))

    unit = re.compile(
        r"(\d[\d,]*(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
        r"(billion|million|trillion|kelvin|years|seconds|tons|eV|K|yr|g/cm³|g/cm3|solar masses|solar radii|%)",
        re.I,
    )
    for m in unit.finditer(plain):
        num, u = m.group(1), m.group(2)
        window = plain[max(0, m.start() - 40) : m.start()]
        words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", window) if w.lower() not in STOP]
        label = " ".join(words[-2:]) if words else ""
        if label:
            add(label, f"{num} {u}")
        if len(out) >= 6:
            break
    return out[:6]


def _charts(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    charts: list[dict[str, Any]] = []
    for table in tables:
        headers = table.get("headers") or []
        rows = table.get("rows") or []
        if len(headers) < 2 or len(rows) < 2:
            continue
        label_idx = 0
        series = []
        for ci, h in enumerate(headers):
            if ci == 0:
                continue
            vals = []
            ok = 0
            for row in rows:
                cell = row[ci] if ci < len(row) else ""
                num = _to_float(cell)
                vals.append(0.0 if num is None else num)
                if num is not None:
                    ok += 1
            if ok >= max(2, math.ceil(len(rows) * 0.5)):
                series.append({"name": h or f"col {ci}", "values": vals})
        labels = [(row[label_idx] if row else "") or f"{i+1}" for i, row in enumerate(rows)]
        if not series:
            continue
        kind = "bar"
        if re.search(r"year|time|age|day|step|stage", str(headers[0]), re.I):
            kind = "line"
        elif len(labels) > 8:
            kind = "hbar"
        scale = "log" if any(_needs_log(s["values"]) for s in series) else "linear"
        charts.append(
            {
                "type": kind,
                "scale": scale,
                "title": headers[0] or "ledger",
                "labels": labels[:16],
                "series": [{**s, "values": s["values"][:16]} for s in series[:3]],
            }
        )
    return charts


def _needs_log(vals: list[float]) -> bool:
    pos = [v for v in vals if v and v > 0]
    if len(pos) < 2:
        return False
    return (max(pos) / min(pos)) >= 40


def _lesson(
    title: str,
    lede: str,
    quotes: list[str],
    tables: list[dict[str, Any]],
    stats: list[dict[str, Any]],
    kind: str,
) -> tuple[str, str, str]:
    idea = ""
    if lede:
        idea = re.split(r"(?<=[.!?])\s+", lede)[0].strip()
    elif quotes:
        idea = quotes[0]
    else:
        idea = title
    if len(idea) > 160:
        idea = idea[:157].rstrip() + "…"

    question = f"What is this chamber about?"
    answer = title
    if tables:
        headers = tables[0].get("headers") or []
        rows = tables[0].get("rows") or []
        ci = None
        best = 0.0
        for i in range(1, len(headers)):
            if re.search(r"note|fate|color|example", str(headers[i]), re.I):
                continue
            pos = []
            for r in rows:
                n = _to_float(r[i] if i < len(r) else "")
                if n and n > 0:
                    pos.append(n)
            if len(pos) < 2:
                continue
            span = max(pos) / min(pos)
            if span > best:
                best, ci = span, i
        if ci is not None and rows:
            pick = next(
                (
                    r
                    for r in rows
                    if re.search(r"sun|g2|proxima", " ".join(r), re.I)
                ),
                None,
            )
            if pick is None:
                ranked = [
                    r
                    for r in rows
                    if _to_float(r[ci] if ci < len(r) else "") is not None
                ]
                pick = ranked[len(ranked) // 2] if ranked else rows[len(rows) // 2]
            name = pick[0] if pick else title
            raw = pick[ci] if ci < len(pick) else ""
            num = _to_float(raw)
            question = f"What is the {headers[ci]} of {name}?"
            answer = _fmt(num) if num is not None else str(raw)
    elif stats:
        question = f"What is the {stats[0]['label']}?"
        answer = stats[0]["value"]
    elif quotes:
        question = "What does this page claim?"
        answer = quotes[0]
    return idea, question, answer


def _kind(
    index: int,
    plain: str,
    blocks: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    images: list[dict[str, Any]],
    stats: list[dict[str, Any]],
    charts: list[dict[str, Any]],
) -> str:
    words = len(plain.split())
    sizes = [float(b.get("size") or 0) for b in blocks]
    big = max(sizes) if sizes else 0
    mean = (sum(sizes) / len(sizes)) if sizes else 0
    if index == 0 and words < 120:
        return KIND_TITLE
    if big > mean * 1.8 and words < 80:
        return KIND_TITLE
    if charts or (tables and stats):
        return KIND_DATA
    if images and words < 90:
        return KIND_FIGURE
    if re.search(r"[=≈≃]\s*\d|\d+\s*[×x]\s*10\^|∫|√|Δ", plain) and words < 160:
        return KIND_FORMULA
    if 40 <= words <= 220 and len(blocks) <= 10:
        return KIND_CONCEPT
    return KIND_NARRATIVE


def _prompt(kind: str, title: str, keywords: list[dict[str, Any]], lede: str) -> str:
    keys = ", ".join(k["word"] for k in keywords[:8])
    mood = {
        KIND_TITLE: "monumental dark observatory, floating glass page, amber holodeck grid floor",
        KIND_DATA: "architectural data field, bars of light, brass instruments, dark museum",
        KIND_CONCEPT: "constellation of ideas as glass orbs, faint gold filaments",
        KIND_FIGURE: "holographic specimen plate, volumetric dust, vitrine lighting",
        KIND_NARRATIVE: "slow cinematic void, typographic architecture, paper-white light",
        KIND_FORMULA: "sculptural numerals in space, orbital rings, spectrograph ticks",
    }[kind]
    snippet = (lede or title)[:180]
    return (
        f"Cinematic holodeck chamber, no readable text, photoreal, rich blacks, film grain. "
        f"Subject: {title}. {mood}. Motifs: {keys}. {snippet}"
    )


def _to_float(text: str) -> float | None:
    if not text:
        return None
    raw = str(text).strip().replace(",", "").replace("×", "x").replace("−", "-")
    if re.search(r"\d.+\d", raw) and re.search(r"[–—]", raw):
        parts = [p for p in re.split(r"[–—]", raw) if p.strip()]
        nums = [_to_float(p) for p in parts]
        nums = [n for n in nums if n is not None]
        return (sum(nums) / len(nums)) if nums else None
    if re.search(r"[A-Za-z]", raw) and not re.search(r"^[-+]?\d", raw):
        return None
    compact = re.sub(r"[^\d.eE+\-]", "", raw)
    if compact in {"", ".", "+", "-", "+.", "-."}:
        return None
    try:
        return float(compact)
    except Exception:
        return None


def _fmt(n: float) -> str:
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if abs(n) >= 10_000:
        return f"{n:,.0f}"
    if abs(n) >= 100:
        return f"{n:,.1f}"
    if abs(n) >= 1:
        return f"{n:.2f}"
    return f"{n:.3g}"


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text
