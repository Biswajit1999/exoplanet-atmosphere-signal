import numpy as np
import pytest
from robustness import gls_template_fit,ar1_covariance,template_injection_recovery

def test_gls_recovers_exact_template():
    x=np.linspace(-1,1,40); X=np.column_stack([np.ones(len(x)),np.exp(-x*x/0.1)])
    beta,cov,chi=gls_template_fit(X@np.array([0.01,0.002]),X,ar1_covariance(40,0.001,0.3))
    assert np.allclose(beta,[0.01,0.002],atol=1e-10) and chi<1e-20
    assert np.linalg.eigvalsh(cov).min()>0

def test_correlation_increases_uncertainty():
    x=np.linspace(-1,1,50);X=np.column_stack([np.ones(len(x)),x])
    _,a,_=gls_template_fit(X@np.array([1.,0.1]),X,ar1_covariance(50,0.1,0))
    _,b,_=gls_template_fit(X@np.array([1.,0.1]),X,ar1_covariance(50,0.1,0.7))
    assert b[0,0]>a[0,0]

def test_injection_coverage():
    x=np.linspace(-1,1,30);X=np.column_stack([np.ones(len(x)),x])
    result=template_injection_recovery(X,ar1_covariance(30,0.1,0.3),[1,0.2],seeds=250,seed=42)
    assert np.all(np.abs(result['bias'])<0.03)
    assert np.all((result['coverage95']>0.88)&(result['coverage95']<0.99))

def test_invalid_covariance():
    with pytest.raises(ValueError): ar1_covariance(5,1,1)
    with pytest.raises(np.linalg.LinAlgError): gls_template_fit(np.ones(5),np.ones((5,1)),-np.eye(5))
