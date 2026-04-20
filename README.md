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

## Usage

Run with Python entry point:

```bash
uv run python main.py input.docx output.pdf
```

Or via lightweight launcher:

```bash
./docx2pdf input.docx output.pdf
```

Overwrite existing output only when explicit:

```bash
uv run python main.py input.docx output.pdf --overwrite
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
├── docx2pdf
├── main.py
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
2. Extend `select_converter(...)` in `main.py` with new input/output routing.
3. Keep CLI unchanged.
