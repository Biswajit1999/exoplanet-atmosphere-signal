"""Deterministic, provenance-recording fetch of the real WASP-39b
transmission-spectrum netCDF product from Zenodo.

Data source: Grant, Lothringer, Wakeford et al. 2023, "Detection of carbon
monoxide's 4.6 micron fundamental band structure in WASP-39b's atmosphere
with JWST NIRSpec G395H", arXiv:2304.11994. Real, published, peer-reviewed
transit-depth measurements and best-fit models, Zenodo DOI
10.5281/zenodo.7866690, file "2_transmission_spectra_and_models.nc"
(60.3 KB, live-verified before this script was written).

This script performs a real network download and must only be invoked with
explicit user authorization for the session.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests

from jwst_wasp39b_evidence_ladder.exceptions import ArchiveAccessError
from jwst_wasp39b_evidence_ladder.logging_utils import get_logger
from jwst_wasp39b_evidence_ladder.provenance import ManifestRow, append_manifest_row, sha256_file

LOGGER = get_logger(__name__)

ZENODO_RECORD_ID = "7866690"
FILE_NAME = "2_transmission_spectra_and_models.nc"
SOURCE_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/{FILE_NAME}/content"
PRODUCT_ID = "wasp39b_grant2023_transmission_spectrum"
LICENCE_TERMS = (
    "Zenodo deposit 10.5281/zenodo.7866690 (Grant, Lothringer, Wakeford et al. 2023, "
    "arXiv:2304.11994), open access; standard Zenodo/CC licence terms apply per the deposit page, "
    "https://zenodo.org/records/7866690"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument(
        "--i-have-authorization",
        action="store_true",
        help=(
            "Required flag confirming the operator has explicitly authorized this "
            "real network download in the current session."
        ),
    )
    args = parser.parse_args()

    if not args.i_have_authorization:
        raise SystemExit(
            "Refusing to download real archive data without --i-have-authorization. "
            "This flag exists so the download only runs after the operator has "
            "explicitly confirmed it in the current session."
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{PRODUCT_ID}.nc"

    LOGGER.info("Downloading %s -> %s", SOURCE_URL, out_path)
    response = requests.get(SOURCE_URL, timeout=60)
    if response.status_code != 200:
        raise ArchiveAccessError(f"download failed: HTTP {response.status_code}")
    out_path.write_bytes(response.content)

    digest = sha256_file(out_path)
    size = out_path.stat().st_size
    row = ManifestRow(
        product_id=PRODUCT_ID,
        source="Zenodo",
        source_url=SOURCE_URL,
        retrieved_utc=datetime.now(timezone.utc).isoformat(),
        sha256=digest,
        file_size_bytes=size,
        selection_reason=(
            "Real published WASP-39b transmission spectrum + full/no-CO nested best-fit "
            "models from Grant et al. (2023), used directly for the evidence-ladder comparison"
        ),
        licence_or_terms=LICENCE_TERMS,
    )
    append_manifest_row(args.manifest, row)
    LOGGER.info("Recorded manifest row for %s (%d bytes)", PRODUCT_ID, size)
    print(f"Downloaded and recorded 1 spectrum file under {args.out_dir}")


if __name__ == "__main__":
    main()
