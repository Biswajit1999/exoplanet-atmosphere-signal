"""Reproduce a synthetic wavelength-bin influence plot; no observational data."""
import numpy as np
import matplotlib.pyplot as plt
from influence import influence

w = np.linspace(1, 5, 50)
x = np.column_stack([np.ones(len(w)), w - 3, np.exp(-0.5*((w-3.5)/0.3)**2)])
sigma = np.full(len(w), 0.1)
y = x @ np.array([1., 0.2, 0.4])
y[30] += 0.5
h, shifts = influence(x, y, sigma)
fig, ax = plt.subplots(2, 1, sharex=True, figsize=(7, 5))
ax[0].plot(w, h, "k.")
ax[0].set_ylabel("Weighted leverage")
ax[1].plot(w, np.linalg.norm(shifts, axis=1), "k.")
ax[1].set_ylabel("LOO coefficient shift norm")
ax[1].set_xlabel("Synthetic wavelength (micrometres)")
fig.tight_layout()
fig.savefig("synthetic_influence.png", dpi=150)
