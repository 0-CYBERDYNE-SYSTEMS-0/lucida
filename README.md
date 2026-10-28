# LUCIDA

Turn each PDF page into a room with text, charts, and locally generated images.
Open the STARFORGE sample or choose your own PDF.

## Download and run

Install Python 3.10 or later. Then download and extract the
[ZIP archive](https://github.com/0-CYBERDYNE-SYSTEMS-0/lucida/archive/refs/heads/main.zip),
or use Git:

```bash
git clone https://github.com/0-CYBERDYNE-SYSTEMS-0/lucida.git
cd lucida
```

On macOS or Linux, run these commands from the extracted project folder:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./run.sh
```

On Windows, use PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server.py
```

Open <http://127.0.0.1:7474>. Select **enter the sample atlas**, or choose a PDF.
The sample has eight pages. The upload limit is 80 MB.
Stop the server with Ctrl+C.

## Controls

- Left/right arrows or `k`/`j`: change pages.
- Space: show or hide the original page.
- `r`: show the recall question.
- `f`: enter or leave fullscreen.

## Privacy and local data

PDF processing and image generation run on your computer. No API key is required.
The page requests display fonts from Google Fonts. These requests send normal connection information to Google.
PDF contents are not sent to Google Fonts.

The server listens on `127.0.0.1`. Use it as a local application.
It has no user login or access controls for public hosting.

Uploaded PDFs, document metadata, extracted text, and generated images stay in `data/<session-id>/`.
The application does not remove these files automatically.
Stop the server and delete the applicable session folder to remove a document and its generated files.
Keep `data/sample/starforge.pdf` to retain the sample.

Git excludes session files, environment files, keys, and local caches.
Check staged files before each commit. Ignore rules do not detect secrets inside source code.

## How it works

- FastAPI serves the application and its local API.
- PyMuPDF extracts page text, tables, and images.
- Pillow generates images locally.
- Plain JavaScript displays each page and its charts.
- Page results are cached for repeated requests.
- Text extraction does not include OCR for scanned pages.

No frontend build is required. The sample uses standard PDF fonts.

## Checks

```bash
.venv/bin/python -m compileall -q server.py lucida
curl http://127.0.0.1:7474/api/health
```

Open the sample and check page changes, images, the original page, and fullscreen.
Upload a PDF and check that repeated page requests use cached results.

## License

LUCIDA is licensed under [AGPL-3.0-or-later](LICENSE).
Dependencies retain their own licenses. PyMuPDF also uses the AGPL license.
