# DOCX to PDF Converter (Local + Private)

High-fidelity DOCX to PDF conversion using LibreOffice headless mode.

## Why this approach

- Local-only execution (no network calls, no cloud APIs)
- High layout fidelity by using LibreOffice's renderer
- Fast and minimal CLI flow
- Easy to extend with new converter backends and formats

## Requirements

- `uv` installed
- LibreOffice installed with `soffice` available in `PATH`

## Easiest usage on macOS

Open `dist/DOCX to PDF.app`, then choose one or more Word documents. You can also
drag DOCX files directly onto the app. Each PDF is saved beside its original DOCX,
so there is no output path to type or remember.

If a PDF with the same name already exists, the app asks before replacing it.
Everything runs locally through LibreOffice; the app makes no network calls.

To build or refresh the app after changing the source:

```bash
uv run --offline python scripts/build_macos_app.py
```

The resulting app is self-contained with respect to this project's Python source,
so it can be moved to `/Applications` or the Desktop. It still requires `uv` and
LibreOffice to be installed on the Mac.

## Battery and performance

- The app runs only when opened or when files are dropped onto it.
- It installs no login item, background service, watcher, or scheduled task.
- LibreOffice exits after each conversion and is limited by a 60-second timeout.
- The app uses an isolated temporary LibreOffice profile and removes it afterward.
- `uv` runs offline, so conversion never performs update or network checks.

## Terminal usage

The short form saves the PDF beside the DOCX:

```bash
./docx2pdf "/any/location/report.docx"
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

## Project Structure

```text
project_root/
├── dist/
│   └── DOCX to PDF.app
├── docx2pdf
├── conversion.py
├── desktop.py
├── main.py
├── scripts/
│   └── build_macos_app.py
├── converters/
│   ├── base.py
│   └── libreoffice.py
├── utils/
│   └── file_ops.py
├── pyproject.toml
└── README.md
```

## Extending later

To add new conversions:

1. Add a new converter class implementing `Converter`.
2. Extend `select_converter(...)` in `conversion.py` with new input/output routing.
3. Keep CLI unchanged.
