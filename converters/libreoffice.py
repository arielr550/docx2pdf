from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from converters.base import Converter

# LibreOffice's .dmg installer does not put soffice on PATH.
MACOS_SOFFICE_CANDIDATES = (
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
)


def find_soffice(binary: str = "soffice") -> str | None:
    found = shutil.which(binary)
    if found is not None:
        return found
    for candidate in MACOS_SOFFICE_CANDIDATES:
        if candidate.is_file():
            return str(candidate)
    return None


class LibreOfficeConverter(Converter):
    def __init__(self, soffice_binary: str = "soffice", timeout_seconds: int = 60) -> None:
        resolved = find_soffice(soffice_binary)
        if resolved is None:
            raise RuntimeError(
                "LibreOffice binary 'soffice' was not found in PATH or /Applications. "
                "Install LibreOffice and ensure 'soffice' is accessible."
            )
        self.soffice_binary = resolved
        self.timeout_seconds = timeout_seconds

    def convert(self, input_path: str, output_path: str) -> None:
        src = Path(input_path)
        dst = Path(output_path)

        # Always render into an empty directory: LibreOffice can exit 0 without
        # writing anything, so an existing PDF at dst must never count as output.
        with tempfile.TemporaryDirectory(prefix="docxpdf_") as temp_dir:
            temp_dir_path = Path(temp_dir)
            result = self._run_soffice(src, temp_dir_path)
            produced = temp_dir_path / f"{src.stem}.pdf"
            if not produced.exists():
                raise RuntimeError(
                    f"LibreOffice did not produce a PDF for {src.name}. "
                    f"stderr='{result.stderr.strip()}'"
                )
            shutil.move(str(produced), str(dst))

    def _run_soffice(self, input_file: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="docxpdf_lo_profile_") as profile_dir:
            command = [
                self.soffice_binary,
                f"-env:UserInstallation={Path(profile_dir).as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(input_file),
            ]
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=self.timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    f"LibreOffice conversion timed out after {self.timeout_seconds} seconds."
                ) from exc
        if result.returncode != 0:
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            raise RuntimeError(
                "LibreOffice conversion command failed "
                f"(exit={result.returncode}). stdout='{stdout}' stderr='{stderr}'"
            )
        return result
