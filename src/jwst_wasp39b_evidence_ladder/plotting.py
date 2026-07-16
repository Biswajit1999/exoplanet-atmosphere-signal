from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def plot_demo(values: np.ndarray, output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(np.arange(values.size), values)
    ax.set_xlabel("Synthetic index")
    ax.set_ylabel("Synthetic value")
    ax.set_title("Smoke-test output — not a scientific result")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path
