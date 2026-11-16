import numpy as np
import pytest
from covariance_audit import ar1_covariance,template_gls,rho_sweep

def test_exact_recovery():
    t=np.array([-2.,-1.,0.,1.,2.])
    a,e=template_gls(8+3*t,t,np.eye(5))
    assert a==pytest.approx(3)
    assert e==pytest.approx(1/np.sqrt(10))

def test_covariance_scaling():
    t=np.array([-1.,0.,1.])
    a,e=template_gls(2*t,t,np.eye(3))
    b,f=template_gls(2*t,t,9*np.eye(3))
    assert a==pytest.approx(b)
    assert f==pytest.approx(3*e)

def test_ar1_covariance():
    c=ar1_covariance([2,3,4],0.5)
    assert np.diag(c)==pytest.approx([4,9,16])
    assert c[0,2]==pytest.approx(2)

def test_zero_correlation():
    t=np.array([-2.,-1.,0.,1.,2.])
    out=rho_sweep(t,t,np.ones(5),[0,0.3])
    assert out[0][1]==pytest.approx(1)
    assert out[0][2]>0

def test_invalid():
    with pytest.raises(ValueError): ar1_covariance([1,2],1)
    with pytest.raises(ValueError): template_gls([1,2],[1,1],np.eye(2))
