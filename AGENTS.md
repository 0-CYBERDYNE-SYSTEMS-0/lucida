# Repository Guidelines

## Project Structure & Module Organization

LUCIDA turns PDF pages into rooms with text, charts, and generated images.

- `server.py` defines FastAPI routes, uploads, sessions, and page caching.
- `lucida/extract.py` extracts PDF content. `analyze.py` classifies pages. `art.py` generates images with Pillow.
- `lucida/sample_book.py` creates the STARFORGE sample PDF.
- `static/` contains the HTML, CSS, and plain JavaScript interface.
- `data/sample/` holds the sample PDF. Other data directories hold uploaded PDFs and generated files.

## Build, Test, and Development Commands

Run these commands from the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```

Open `http://127.0.0.1:7474`. The server serves static files directly; no frontend build is required.

- `curl http://127.0.0.1:7474/api/health` checks the running server.
- `.venv/bin/python -m compileall -q server.py lucida` checks Python syntax.

## Coding Style & Naming Conventions

Use four spaces for Python indentation and two spaces for JavaScript and CSS. Match the surrounding code.
Use Python type hints, `snake_case` function names, and uppercase constants.
Use `camelCase` for JavaScript functions and variables.
Keep page filenames zero-padded, such as `000.json` and `000_plate.jpg`.
No formatter or lint configuration is included. Keep changes limited to the task.

## Testing Guidelines

No automated test suite or coverage threshold is configured. Syntax checks do not replace behavior checks.
Start the server and open STARFORGE. Check page navigation, generated images, original-page display, and fullscreen controls.
Upload a PDF and check that its pages load. Confirm that repeated page requests use cached results.
For new automated tests, use descriptive `test_*.py` filenames and document the command and dependencies.

## Commit & Pull Request Guidelines

This directory has no Git metadata. Commit message conventions cannot be confirmed from local history.
Use short, action-based commit subjects. Describe the change, related issue, and verification results in each pull request.
Include screenshots for interface changes.

Preserve contributor authorship. Before declaring a pull request ready, check:

```bash
git config user.name
git config user.email
git log --format='%h %an <%ae> %s'
```

Use `0-CYBERDYNE-SYSTEMS-0 <134018026+0-CYBERDYNE-SYSTEMS-0@users.noreply.github.com>` unless the owner specifies another verified identity.

## Data Handling

Keep uploaded PDFs and generated session files out of commits. Preserve the sample PDF exception in `.gitignore`.
