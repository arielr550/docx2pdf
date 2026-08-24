from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from conversion import convert_document, default_output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local, private DOCX to PDF converter powered by LibreOffice."
    )
    parser.add_argument("input_file", help="Path to input DOCX file.")
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Optional output PDF path. Defaults to beside the input file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting output file if it already exists.",
    )
    return parser


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    output_path = (
        Path(args.output_file).expanduser().resolve()
        if args.output_file
        else default_output_path(input_path)
    )

    logging.info(
        "Conversion started: input=%s output=%s engine=libreoffice",
        input_path,
        output_path,
    )

    try:
        convert_document(input_path, output_path, overwrite=args.overwrite)
    except Exception as exc:
        logging.error("Conversion failed: %s", exc)
        return 1

    logging.info("Conversion succeeded: output=%s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
