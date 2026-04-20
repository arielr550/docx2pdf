from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from converters.base import Converter
from converters.libreoffice import LibreOfficeConverter
from utils.file_ops import ensure_supported_input, validate_input_path, validate_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local, private DOCX to PDF converter powered by LibreOffice."
    )
    parser.add_argument("input_file", help="Path to input DOCX file.")
    parser.add_argument("output_file", help="Path to output PDF file.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting output file if it already exists.",
    )
    return parser


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def select_converter(input_path: Path, output_path: Path) -> Converter:
    if input_path.suffix.lower() == ".docx" and output_path.suffix.lower() == ".pdf":
        return LibreOfficeConverter()
    raise ValueError(
        f"Unsupported conversion: {input_path.suffix or '<no suffix>'} -> "
        f"{output_path.suffix or '<no suffix>'}"
    )


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    output_path = Path(args.output_file).expanduser().resolve()

    try:
        validate_input_path(input_path)
        validate_output_path(output_path, overwrite=args.overwrite)
        ensure_supported_input(input_path)
        converter = select_converter(input_path, output_path)
    except Exception as exc:
        logging.error("Conversion failed: %s", exc)
        return 1

    logging.info(
        "Conversion started: input=%s output=%s engine=libreoffice",
        input_path,
        output_path,
    )

    try:
        converter.convert(str(input_path), str(output_path))
    except Exception as exc:
        logging.error("Conversion failed: %s", exc)
        return 1

    logging.info("Conversion succeeded: output=%s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
