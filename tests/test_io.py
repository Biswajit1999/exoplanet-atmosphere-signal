from __future__ import annotations


import numpy as np
import pytest

try:
    import netCDF4
    HAVE_NETCDF4 = True
except ImportError:
    HAVE_NETCDF4 = False

from jwst_wasp39b_evidence_ladder.exceptions import DataSchemaError
from jwst_wasp39b_evidence_ladder.io import REQUIRED_VARIABLES, load_spectrum


def test_load_spectrum_raises_on_missing_file(tmp_path):
    with pytest.raises(DataSchemaError):
        load_spectrum(tmp_path / "does_not_exist.nc")


@pytest.mark.skipif(not HAVE_NETCDF4, reason="netCDF4 not installed")
def test_load_spectrum_raises_on_missing_variables(tmp_path):
    path = tmp_path / "incomplete.nc"
    with netCDF4.Dataset(path, "w") as ds:
        ds.createDimension("n", 5)
        var = ds.createVariable("wavelength_native_resolution", "f8", ("n",))
        var[:] = np.linspace(4.0, 5.2, 5)
    with pytest.raises(DataSchemaError):
        load_spectrum(path)


@pytest.mark.skipif(not HAVE_NETCDF4, reason="netCDF4 not installed")
def test_load_spectrum_sorts_by_wavelength_and_reads_all_variables(tmp_path):
    path = tmp_path / "complete.nc"
    n = 5
    wl = np.array([5.0, 4.0, 4.5, 4.2, 4.8])
    with netCDF4.Dataset(path, "w") as ds:
        ds.createDimension("n", n)
        for name in REQUIRED_VARIABLES:
            var = ds.createVariable(name, "f8", ("n",))
            if name == "wavelength_native_resolution":
                var[:] = wl
            else:
                var[:] = np.full(n, 0.02)
    spectrum = load_spectrum(path)
    assert np.all(np.diff(spectrum.wavelength_um) > 0)
    assert spectrum.wavelength_um.size == n
