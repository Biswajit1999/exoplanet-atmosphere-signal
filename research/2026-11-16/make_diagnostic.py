"""Regenerate a clearly synthetic conditional covariance sensitivity plot."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from covariance_audit import rho_sweep

x=np.linspace(-1,1,25)
template=np.exp(-0.5*(x/0.23)**2)
y=2.0+0.003*x+0.12*template
rhos=np.linspace(-0.8,0.8,33)
values=rho_sweep(y,template,np.full(len(x),0.03),rhos)
fig,ax=plt.subplots()
ax.plot(rhos,[v[2] for v in values])
ax.set(xlabel="Assumed adjacent-bin correlation",ylabel="Conditional amplitude standard error",title="Synthetic GLS covariance sensitivity")
fig.tight_layout()
fig.savefig("synthetic_covariance_sensitivity.png",dpi=160)
