from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from converters.base import Converter


class LibreOfficeConverter(Converter):
    def __init__(self, soffice_binary: str = "soffice") -> None:
        self.soffice_binary = soffice_binary
        self._assert_soffice_available()

    def convert(self, input_path: str, output_path: str) -> None:
        src = Path(input_path)
        dst = Path(output_path)

        expected_pdf_name = f"{src.stem}.pdf"
        can_write_directly = dst.name == expected_pdf_name

        if can_write_directly:
            self._run_soffice(src, dst.parent)
            produced = dst.parent / expected_pdf_name
            if not produced.exists():
                raise RuntimeError(
                    f"LibreOffice did not produce expected output file: {produced}"
                )
            return

        with tempfile.TemporaryDirectory(prefix="docxpdf_") as temp_dir:
            temp_dir_path = Path(temp_dir)
            self._run_soffice(src, temp_dir_path)
            produced = temp_dir_path / expected_pdf_name
            if not produced.exists():
                raise RuntimeError(
                    f"LibreOffice did not produce expected output file: {produced}"
                )
            shutil.move(str(produced), str(dst))

    def _assert_soffice_available(self) -> None:
        if shutil.which(self.soffice_binary) is None:
            raise RuntimeError(
                "LibreOffice binary 'soffice' was not found in PATH. "
                "Install LibreOffice and ensure 'soffice' is accessible."
            )

    def _run_soffice(self, input_file: Path, output_dir: Path) -> None:
        command = [
            self.soffice_binary,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_file),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            raise RuntimeError(
                "LibreOffice conversion command failed "
                f"(exit={result.returncode}). stdout='{stdout}' stderr='{stderr}'"
            )
