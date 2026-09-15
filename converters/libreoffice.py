from __future__ import annotations

import fcntl
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from converters.base import Converter

# LibreOffice's .dmg installer does not put soffice on PATH.
MACOS_SOFFICE_CANDIDATES = (
    Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
)

# Name the import filter explicitly. Without it LibreOffice falls back to its
# plain-text importer for unreadable files and "successfully" renders the raw
# bytes as a PDF instead of failing.
INPUT_FILTERS = {
    ".docx": "MS Word 2007 XML",
}


def find_soffice(binary: str = "soffice") -> str | None:
    found = shutil.which(binary)
    if found is not None:
        # Launching LibreOffice through a symlink such as /usr/local/bin/soffice
        # adds about 1.5 seconds of startup on macOS.
        return os.path.realpath(found)
    for candidate in MACOS_SOFFICE_CANDIDATES:
        if candidate.is_file():
            return str(candidate)
    return None


def clean_stderr(stderr: str) -> str:
    # soffice logs this harmless line on every headless launch on macOS.
    lines = [line for line in stderr.splitlines() if "Task policy set failed" not in line]
    return "\n".join(lines).strip()


def profile_cache_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "docx2pdf" / "lo-profile"


@contextmanager
def libreoffice_profile() -> Iterator[Path]:
    """Yield a LibreOffice user profile directory for one soffice run.

    A reused profile skips LibreOffice's first-start setup. Two soffice
    processes must not share a profile, so the cached one is used only while
    holding its lock; a concurrent run gets a throwaway profile instead.
    """
    cache = profile_cache_dir()
    with ExitStack() as stack:
        profile = cache
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            lock = stack.enter_context(open(cache.parent / "lo-profile.lock", "w"))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            profile = Path(
                stack.enter_context(tempfile.TemporaryDirectory(prefix="docxpdf_lo_profile_"))
            )
        yield profile


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
                    f"stderr='{clean_stderr(result.stderr)}'"
                )
            shutil.move(str(produced), str(dst))

    def _run_soffice(self, input_file: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
        with libreoffice_profile() as profile_dir:
            command = [
                self.soffice_binary,
                f"-env:UserInstallation={profile_dir.as_uri()}",
                "--headless",
            ]
            input_filter = INPUT_FILTERS.get(input_file.suffix.lower())
            if input_filter is not None:
                command.append(f"--infilter={input_filter}")
            command += [
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
            stderr = clean_stderr(result.stderr)
            raise RuntimeError(
                "LibreOffice conversion command failed "
                f"(exit={result.returncode}). stdout='{stdout}' stderr='{stderr}'"
            )
        return result
