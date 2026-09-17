# DocZap

Fast, local, private DOCX to PDF conversion that keeps the layout intact, using LibreOffice headless mode.

## Why this approach

- Local-only execution (no network calls, no cloud APIs)
- High layout fidelity by using LibreOffice's renderer
- Fast and minimal CLI flow
- Easy to extend with new converter backends and formats

## Requirements

- `uv` installed (Homebrew or the official installer)
- LibreOffice installed, either via `brew install --cask libreoffice` or the
  `.dmg` into `/Applications`. `soffice` is found on `PATH` or inside
  `LibreOffice.app`.
- Python 3.10 or newer, which `uv` can provide

## Easiest usage on macOS

Build the app once (and again after changing the source):

```bash
uv run --offline python scripts/build_macos_app.py
```

Open `dist/DocZap.app`, then choose one or more Word documents. You can also
drag DOCX files directly onto the app. Each PDF is saved beside its original DOCX,
so there is no output path to type or remember.

If a PDF with the same name already exists, the app asks before replacing it.
Everything runs locally through LibreOffice; the app makes no network calls.
Images a document only links to on the web are not downloaded, so they are left
out of the PDF.

The app is self-contained with respect to this project's Python source, so it can
be moved to `/Applications` or the Desktop. It still requires `uv` and LibreOffice
to be installed on the Mac. `dist/` is a build output and is not committed.

## Battery and performance

- The app runs only when opened or when files are dropped onto it.
- It installs no login item, background service, watcher, or scheduled task.
- LibreOffice exits after each conversion and is limited by a 60-second timeout.
- LibreOffice uses a private profile cached in `~/Library/Caches/doczap/lo-profile`
  (about 0.5 MB), which skips its first-start setup on every conversion. A
  concurrent conversion gets a temporary profile instead of sharing it. Delete the
  folder to reset it.
- `uv` runs offline, so conversion never performs update or network checks.

## Terminal usage

The short form saves the PDF beside the DOCX:

```bash
./doczap "/any/location/report.docx"
```

You can drag a file from Finder into Terminal instead of typing its path.

To choose a different output path:

```bash
uv run --offline python main.py input.docx output.pdf
```

Overwrite existing output only when explicit:

```bash
uv run --offline python main.py input.docx output.pdf --overwrite
```

## Behavior

- Validates input exists and is a file
- Validates output path and blocks overwrite by default
- Fails clearly if format is unsupported
- Fails clearly if `soffice` is missing
- Uses `soffice --headless --convert-to pdf` for rendering fidelity
- Renders into a temporary directory and only then moves the PDF into place, so a
  failed conversion never leaves an old PDF looking like fresh output

## Fonts and fidelity

Pagination only matches Word when the document's fonts are available to
LibreOffice. Microsoft's defaults (Calibri, Cambria) are usually missing on a Mac,
and Microsoft Office for Mac keeps its fonts inside its own app bundle where
LibreOffice cannot see them. Missing fonts are silently substituted, which shifts
line breaks and page counts.

Install the metric-compatible replacements to keep layout stable:

```bash
brew install --cask font-carlito font-caladea
```

For other fonts (for example Aptos), install the actual font files system-wide.
