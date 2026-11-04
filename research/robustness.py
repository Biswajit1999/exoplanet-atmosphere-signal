"""Conditional covariance and injection diagnostics for spectral templates."""
import numpy as np


def gls_template_fit(depth, design, covariance):
    """Full-covariance linear template fit with absolute conditional errors."""
    y=np.asarray(depth,float)
    X=np.asarray(design,float)
    C=np.asarray(covariance,float)
    if y.ndim!=1 or X.ndim!=2 or X.shape[0]!=len(y) or C.shape!=(len(y),len(y)) or len(y)<=X.shape[1]:
        raise ValueError('incompatible dimensions')
    if not all(np.isfinite(v).all() for v in (y,X,C)) or not np.allclose(C,C.T):
        raise ValueError('nonfinite or asymmetric inputs')
    L=np.linalg.cholesky(C)
    A=np.linalg.solve(L,X)
    b=np.linalg.solve(L,y)
    info=A.T@A
    cov=np.linalg.inv(info)
    beta=cov@(A.T@b)
    resid=b-A@beta
    return beta,cov,float(resid@resid/(len(y)-X.shape[1]))


def ar1_covariance(n, sigma, rho):
    """Stationary covariance for equally spaced spectral bins (toy model)."""
    if n<1 or sigma<=0 or not np.isfinite(sigma) or not -1<rho<1:
        raise ValueError('invalid covariance parameters')
    idx=np.arange(n)
    return sigma*sigma*rho**np.abs(idx[:,None]-idx[None,:])


def template_injection_recovery(design, covariance, coefficients, seeds=100, seed=1):
    """Parametric Gaussian injections, reporting bias and interval coverage."""
    X=np.asarray(design,float)
    beta=np.asarray(coefficients,float)
    C=np.asarray(covariance,float)
    if X.ndim!=2 or beta.shape!=(X.shape[1],) or seeds<2:
        raise ValueError('invalid injection parameters')
    L=np.linalg.cholesky(C)
    rng=np.random.default_rng(seed)
    recovered=[]
    standard_errors=[]
    for _ in range(seeds):
        y=X@beta+L@rng.standard_normal(len(X))
        fitted,cov,_=gls_template_fit(y,X,C)
        recovered.append(fitted)
        standard_errors.append(np.sqrt(np.diag(cov)))
    estimates=np.asarray(recovered)
    errors=np.asarray(standard_errors)
    return {'bias':np.mean(estimates-beta,axis=0), 'coverage95':np.mean(np.abs(estimates-beta)<=1.96*errors,axis=0), 'empirical_std':np.std(estimates,axis=0,ddof=1)}
