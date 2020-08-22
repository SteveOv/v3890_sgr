import numpy as np
from typing import List
from astropy.units import Quantity
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from astropy.modeling.fitting import LevMarLSQFitter
from specutils import SpectralRegion
from specutils.manipulation.estimate_uncertainty import noise_region_uncertainty
from spectroscopy import Spectrum1DEx, fit_utilities


def fit_b_e_20190905_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_region = Spectrum1DEx.spectral_region_over(4700, 4900)
    noise_spectrum = noise_region_uncertainty(spectrum, noise_region)

    h_beta = Gaussian1D(amplitude=2e-12, mean=4861, stddev=2) + Polynomial1D(degree=1, name="continuum")
    h_beta.name = "H$\\beta$"

    fitter = LevMarLSQFitter()
    fit = fitter(h_beta, noise_spectrum.wavelength, noise_spectrum.flux,
                 weights=np.divide(1, np.power(noise_spectrum.uncertainty.quantity, 2)))
    print(f"{spectrum.name}: " + fit_utilities.describe_compound_fit(fit))
    return [fit]


def fit_r_e_20190905_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_region = Spectrum1DEx.spectral_region_over(6300, 6700)
    noise_spectrum = noise_region_uncertainty(spectrum, noise_region)

    # H-alpha double Gaussian - asymmetric expansion
    h_alpha = Gaussian1D(amplitude=4e-12, mean=6563, stddev=2, name="1") \
        + Gaussian1D(amplitude=2e-12, mean=6563, stddev=30, bounds={"mean": (6560, 6565), "stddev": (20, 50)}, name="2") \
        + Polynomial1D(degree=1, name="continuum")
    h_alpha.name = "H$\\alpha$"

    fitter = LevMarLSQFitter()
    fit = fitter(h_alpha, noise_spectrum.wavelength, noise_spectrum.flux,
                 weights=np.divide(1, np.power(noise_spectrum.uncertainty.quantity, 2)))
    print(f"{spectrum.name}: " + fit_utilities.describe_compound_fit(fit))
    return [fit]

