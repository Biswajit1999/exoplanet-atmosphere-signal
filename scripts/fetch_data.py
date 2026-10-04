"""Refetch and verify all files in the Grant et al. (2023) Zenodo record."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import requests

RECORD = "https://zenodo.org/api/records/7866690/files"
FILES = {
    "wasp39b_grant2023_light_curves.nc": ("1_light_curves.nc", "5416546a1b35b3039d2c03af942bd7446851f352f643f58917e9af0269c1ea97"),
    "wasp39b_grant2023_transmission_spectrum.nc": ("2_transmission_spectra_and_models.nc", "61c05c570ca39854b43b8958e44e97cd229710e6ecec2769a951b5d1b715fb95"),
    "wasp39b_grant2023_co_sub_band_samples.nc": ("3_co_sub_band_samples.nc", "5fb4e75e1366b8b12f21c4317cc78e292dc713b92d52c278e35d3f5b4caeb4a0"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--i-have-authorization", action="store_true")
    args = parser.parse_args()
    if not args.i_have_authorization:
        raise SystemExit("Refusing network download without --i-have-authorization")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for local_name, (remote_name, expected) in FILES.items():
        response = requests.get(f"{RECORD}/{remote_name}/content", timeout=180)
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        if digest != expected:
            raise SystemExit(f"checksum mismatch for {remote_name}: {digest}")
        (args.out_dir / local_name).write_bytes(response.content)
        print(f"verified {local_name} ({len(response.content):,} bytes)")


if __name__ == "__main__":
    main()
