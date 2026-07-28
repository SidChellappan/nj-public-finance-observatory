"""Download and verify the pinned NJ DCA source workbook."""

from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

from . import RAW_WORKBOOK, SOURCE_SHA256, SOURCE_WORKBOOK_URL


class SourceVerificationError(RuntimeError):
    """Raised when the source workbook does not match the pinned checksum."""


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source(path: Path, expected_sha256: str = SOURCE_SHA256) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Source workbook not found: {path}")
    actual = sha256_file(path)
    if actual.lower() != expected_sha256.lower():
        raise SourceVerificationError(
            "Source workbook checksum mismatch. "
            f"Expected {expected_sha256}; found {actual}. "
            "Do not rebuild public artifacts until the changed source is reviewed."
        )
    return actual


def download_source(
    destination: Path = RAW_WORKBOOK,
    *,
    url: str = SOURCE_WORKBOOK_URL,
    expected_sha256: str = SOURCE_SHA256,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f"{destination.name}.download")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NJ-Public-Finance-Observatory/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    handle.write(chunk)
        verify_source(temporary, expected_sha256)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def ensure_source(path: Path = RAW_WORKBOOK) -> Path:
    if not path.exists():
        download_source(path)
    verify_source(path)
    return path


def main() -> None:
    path = ensure_source()
    print(f"Verified source workbook: {path}")
    print(f"SHA-256: {sha256_file(path)}")


if __name__ == "__main__":
    main()
