from __future__ import annotations

import plistlib
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = PROJECT_ROOT / "dist"
APP_PATH = DIST_DIR / "DOCX to PDF.app"
APP_SOURCE_FILES = ("main.py", "desktop.py", "conversion.py", "pyproject.toml", "uv.lock")
APP_SOURCE_DIRS = ("converters", "utils")
UNUSED_PRIVACY_KEYS = (
    "NSAppleEventsUsageDescription",
    "NSAppleMusicUsageDescription",
    "NSCalendarsUsageDescription",
    "NSCameraUsageDescription",
    "NSContactsUsageDescription",
    "NSHomeKitUsageDescription",
    "NSMicrophoneUsageDescription",
    "NSPhotoLibraryUsageDescription",
    "NSRemindersUsageDescription",
    "NSSiriUsageDescription",
    "NSSystemAdministrationUsageDescription",
)

APPLESCRIPT = r'''
use scripting additions

on convertFiles(selectedFiles)
    set runnerPath to (POSIX path of (path to me)) & "Contents/Resources/run-converter"
    set commandText to quoted form of runnerPath

    repeat with selectedFile in selectedFiles
        set commandText to commandText & space & quoted form of POSIX path of selectedFile
    end repeat

    try
        set resultMessage to do shell script commandText
        display notification resultMessage with title "DOCX to PDF"
    on error errorMessage number errorNumber
        if errorNumber is not -128 then
            display alert "Conversion failed" message errorMessage as critical
        end if
    end try
end convertFiles

on run
    try
        set selectedFiles to choose file with prompt "Choose DOCX files to convert" ¬
            of type {"org.openxmlformats.wordprocessingml.document"} ¬
            with multiple selections allowed
        convertFiles(selectedFiles)
    on error errorMessage number errorNumber
        if errorNumber is not -128 then
            display alert "Could not select files" as critical
        end if
    end try
end run

on open droppedFiles
    convertFiles(droppedFiles)
end open
'''

RUNNER = r'''#!/bin/sh
set -eu

RESOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR="$RESOURCE_DIR/project"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export UV_CACHE_DIR="${TMPDIR:-/tmp}/docxpdf-uv-cache"
export PYTHONDONTWRITEBYTECODE=1

if command -v uv >/dev/null 2>&1; then
    UV_BINARY=$(command -v uv)
else
    osascript -e 'display alert "DOCX to PDF needs uv" message "Install uv, then open the app again." as critical'
    exit 1
fi

exec "$UV_BINARY" run --offline --no-project --python 3.14 python "$PROJECT_DIR/desktop.py" "$@"
'''


def compile_applescript() -> None:
    DIST_DIR.mkdir(exist_ok=True)
    if APP_PATH.exists():
        shutil.rmtree(APP_PATH)

    with tempfile.NamedTemporaryFile("w", suffix=".applescript", delete=False) as source:
        source.write(APPLESCRIPT)
        source_path = Path(source.name)

    try:
        result = subprocess.run(
            ["osacompile", "-o", str(APP_PATH), str(source_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"Could not compile the macOS app: {reason}")
    finally:
        source_path.unlink(missing_ok=True)


def copy_runtime() -> None:
    resources = APP_PATH / "Contents" / "Resources"
    bundled_project = resources / "project"
    bundled_project.mkdir()

    for file_name in APP_SOURCE_FILES:
        shutil.copy2(PROJECT_ROOT / file_name, bundled_project / file_name)
    for directory_name in APP_SOURCE_DIRS:
        shutil.copytree(
            PROJECT_ROOT / directory_name,
            bundled_project / directory_name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    runner_path = resources / "run-converter"
    runner_path.write_text(RUNNER, encoding="utf-8")
    runner_path.chmod(runner_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def configure_app() -> None:
    plist_path = APP_PATH / "Contents" / "Info.plist"
    with plist_path.open("rb") as plist_file:
        info = plistlib.load(plist_file)

    for key in UNUSED_PRIVACY_KEYS:
        info.pop(key, None)

    info.update(
        {
            "CFBundleIdentifier": "local.docxpdf.converter",
            "CFBundleName": "DOCX to PDF",
            "CFBundleDisplayName": "DOCX to PDF",
            "CFBundleShortVersionString": "1.0",
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Word Document",
                    "CFBundleTypeRole": "Editor",
                    "LSHandlerRank": "Alternate",
                    "LSItemContentTypes": [
                        "org.openxmlformats.wordprocessingml.document"
                    ],
                }
            ],
        }
    )

    with plist_path.open("wb") as plist_file:
        plistlib.dump(info, plist_file)


def sign_app() -> None:
    result = subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(APP_PATH)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Could not sign the macOS app: {reason}")


def main() -> None:
    compile_applescript()
    copy_runtime()
    configure_app()
    sign_app()
    print(f"Built {APP_PATH}")


if __name__ == "__main__":
    main()
