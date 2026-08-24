from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from conversion import convert_document, default_output_path
from converters.libreoffice import LibreOfficeConverter
from desktop import format_summary


class ConversionTests(unittest.TestCase):
    def test_default_output_is_beside_input(self) -> None:
        self.assertEqual(
            default_output_path(Path("/documents/report.docx")),
            Path("/documents/report.pdf"),
        )

    def test_convert_document_uses_default_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.docx"
            input_path.touch()
            converter = Mock()

            with patch("conversion.select_converter", return_value=converter):
                result = convert_document(input_path)

            expected = input_path.resolve().with_suffix(".pdf")
            self.assertEqual(result, expected)
            converter.convert.assert_called_once_with(str(input_path.resolve()), str(expected))

    def test_existing_default_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "report.docx"
            output_path = Path(temp_dir) / "report.pdf"
            input_path.touch()
            output_path.touch()

            with self.assertRaises(FileExistsError):
                convert_document(input_path)

    def test_desktop_summary_reports_batch_and_skips(self) -> None:
        converted = [Path("one.pdf"), Path("two.pdf")]
        self.assertEqual(
            format_summary(converted, skipped=1),
            "Created 2 PDFs beside the originals. Skipped 1 existing file.",
        )

    def test_libreoffice_timeout_is_bounded_and_reported(self) -> None:
        timeout = subprocess.TimeoutExpired(cmd=["soffice"], timeout=1)
        with (
            patch("converters.libreoffice.shutil.which", return_value="/usr/bin/soffice"),
            patch("converters.libreoffice.subprocess.run", side_effect=timeout),
        ):
            converter = LibreOfficeConverter(timeout_seconds=1)
            with self.assertRaisesRegex(RuntimeError, "timed out after 1 seconds"):
                converter._run_soffice(Path("input.docx"), Path("."))


if __name__ == "__main__":
    unittest.main()
