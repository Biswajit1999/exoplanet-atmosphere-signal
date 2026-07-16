from __future__ import annotations

import csv
import subprocess
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def sha256_config(path: str | Path) -> str | None:
    config_path = Path(path)
    if not config_path.is_file():
        return None
    return sha256_file(config_path)


def get_git_commit(repo_root: str | Path) -> str:
    """Return the current git commit hash, or a sentinel if not a git repo.

    Never raises: this project intentionally has no git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    return "LOCAL_UNCOMMITTED"


_MANIFEST_COLUMNS = (
    "product_id", "source", "source_url", "retrieved_utc", "sha256",
    "file_size_bytes", "selection_reason", "licence_or_terms",
)


@dataclass(frozen=True)
class ManifestRow:
    product_id: str
    source: str
    source_url: str
    retrieved_utc: str
    sha256: str
    file_size_bytes: int
    selection_reason: str
    licence_or_terms: str


def append_manifest_row(path: str | Path, row: ManifestRow) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not manifest_path.is_file()
    with manifest_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_MANIFEST_COLUMNS), quoting=csv.QUOTE_MINIMAL)
        if is_new:
            writer.writeheader()
        writer.writerow(asdict(row))


def read_manifest(path: str | Path) -> list[dict[str, str]]:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        return []
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
