"""Conditional GLS template-amplitude and AR(1) covariance sensitivity."""
import numpy as np

def ar1_covariance(sigma, rho):
    s = np.asarray(sigma, float)
    if s.ndim != 1 or not len(s) or not np.all(np.isfinite(s)) or np.any(s <= 0):
        raise ValueError("positive finite sigma vector required")
    if not np.isfinite(rho) or abs(rho) >= 1:
        raise ValueError("stationary AR1 requires |rho|<1")
    i = np.arange(len(s))
    return np.outer(s, s) * rho ** np.abs(i[:, None]-i[None, :])

def template_gls(y, template, covariance, intercept=True):
    y, t, c = np.asarray(y,float), np.asarray(template,float), np.asarray(covariance,float)
    if y.ndim != 1 or t.shape != y.shape or c.shape != (len(y),len(y)) or not all(np.all(np.isfinite(z)) for z in (y,t,c)):
        raise ValueError("invalid shapes or nonfinite values")
    if not np.allclose(c,c.T,rtol=1e-10,atol=1e-12):
        raise ValueError("covariance must be symmetric")
    x = np.column_stack((np.ones(len(y)),t)) if intercept else t[:,None]
    try:
        z = np.linalg.solve(c,x)
        cb = np.linalg.inv(x.T@z)
        beta = cb@(z.T@y)
    except np.linalg.LinAlgError as exc:
        raise ValueError("singular covariance or design") from exc
    if np.linalg.eigvalsh(c).min() <= 0 or cb[-1,-1] <= 0:
        raise ValueError("nonpositive covariance")
    return float(beta[-1]), float(np.sqrt(cb[-1,-1]))

def rho_sweep(y,template,sigma,rhos):
    return [(float(r),*template_gls(y,template,ar1_covariance(sigma,r))) for r in rhos]
