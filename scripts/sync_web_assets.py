"""Copy generated results/ and figures/ into web-react/public/ so the
dashboard reads real generated output rather than hard-coded values.

Run after scripts/run_analysis.py and scripts/make_figures.py.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def sync(results_dir: Path, figures_dir: Path, manifest_path: Path, web_public_dir: Path) -> None:
    dest_results = web_public_dir / "results"
    dest_figures = web_public_dir / "figures"
    dest_results.mkdir(parents=True, exist_ok=True)
    dest_figures.mkdir(parents=True, exist_ok=True)

    copied = []
    for name in ("summary.json", "warnings.json", "benchmarks.json"):
        src = results_dir / name
        if src.is_file():
            shutil.copy2(src, dest_results / name)
            copied.append(str(src))

    for src in figures_dir.glob("*.svg"):
        shutil.copy2(src, dest_figures / src.name)
        copied.append(str(src))
    for src in figures_dir.glob("*.json"):
        shutil.copy2(src, dest_figures / src.name)
        copied.append(str(src))

    if manifest_path.is_file():
        shutil.copy2(manifest_path, web_public_dir / "manifest.csv")
        copied.append(str(manifest_path))

    print(f"Synced {len(copied)} files into {web_public_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--figures-dir", type=Path, default=Path("figures"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument("--web-public-dir", type=Path, default=Path("web-react/public"))
    args = parser.parse_args()
    sync(args.results_dir, args.figures_dir, args.manifest, args.web_public_dir)


if __name__ == "__main__":
    main()
