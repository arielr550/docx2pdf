from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from conversion import convert_document
from converters.libreoffice import find_soffice

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCUMENT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>Hello from docx2pdf</w:t></w:r></w:p></w:body>
</w:document>"""


def write_minimal_docx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as docx:
        docx.writestr("[Content_Types].xml", CONTENT_TYPES)
        docx.writestr("_rels/.rels", RELS)
        docx.writestr("word/document.xml", DOCUMENT)


@unittest.skipUnless(find_soffice(), "LibreOffice (soffice) is not installed")
class LibreOfficeIntegrationTests(unittest.TestCase):
    def test_real_conversion_produces_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "hello.docx"
            write_minimal_docx(input_path)

            output_path = convert_document(input_path)

            self.assertTrue(output_path.read_bytes().startswith(b"%PDF"))

    def test_unreadable_document_fails_even_when_pdf_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "broken.docx"
            input_path.write_bytes(b"not a zip file")
            stale = input_path.with_suffix(".pdf")
            stale.write_bytes(b"old pdf")

            with self.assertRaises(RuntimeError):
                convert_document(input_path, overwrite=True)

            self.assertEqual(stale.read_bytes(), b"old pdf")


if __name__ == "__main__":
    unittest.main()
