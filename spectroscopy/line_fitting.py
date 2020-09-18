import numpy as np
from copy import copy
from datetime import datetime
from typing import List, Tuple, Union
from astropy.units import si
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from astropy.modeling.fitting import LevMarLSQFitter
from specutils import SpectralRegion, Spectrum1D
from specutils.fitting.continuum import fit_generic_continuum
from spectroscopy import Spectrum1DEx, fit_utilities

_b_e_exclusion_regions = SpectralRegion([(3900, 4150), (4300, 4700), (4800, 4950), (4960, 5080)] * si.AA)

_r_e_exclusion_regions = SpectralRegion([(5900, 6100), (6450, 6750)] * si.AA)


def fit(spectrum: Spectrum1DEx, key: str = None) -> List[CompoundModel]:
    """
    This is the switchboard method for the spectral fitting.
    If it can find a specific method to do the fitting it'll call that, otherwise it falls back on to generic methods.
    """
    this_module = __import__(__name__)
    method = f"fit_{key if key is not None else spectrum.name}"
    if hasattr(this_module, method):
        func = getattr(this_module, method)
    elif spectrum.is_blue:
        func = fit_blue_arm_spectrum
    else:
        func = fit_red_arm_spectrum
    return func(spectrum)


@fit_utilities.trace_fitting
def fit_blue_arm_spectrum(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    # Derive the uncertainties in the spectrum from the noise. We use this for fitting as it provides weighting.
    unc_spec = spectrum.to_uncertainty_spectrum(Spectrum1DEx.spectral_region_over(4700, 4900, si.AA))

    # Work out the continuum model
    cont_model = _continuum_fit(unc_spec)

    # The hints for H-beta.  Early ones are a single Gaussian but later are double.
    if unc_spec.obs_date < datetime(2019, 8, 30):
        beta_hint = _named_gaussian(amplitude=5e-12, mean=4861.4, stddev=35, subscript="1")
    else:
        beta_hint = _named_gaussian(amplitude=4e-12, mean=(4855, 4865), stddev=(1, 10), subscript="2") \
                    + _named_gaussian(amplitude=2e-12, mean=(4855, 4865), stddev=(10, 50), subscript="1")

    # The hints of H-gamma.  Early ones are a single Gaussian but later are double.
    if unc_spec.obs_date < datetime(2019, 8, 30):
        gamma_hint = _named_gaussian(amplitude=2e-12, mean=4340.5, stddev=25, subscript="1")
    else:
        gamma_hint = _named_gaussian(amplitude=4e-12, mean=(4335, 4345), stddev=(1, 7), subscript="2") \
                    + _named_gaussian(amplitude=2e-12, mean=(4335, 4345), stddev=(7, 50), subscript="1")

    # The hints for H-delta.  Early ones are a single Gaussian but later ones are double.
    if unc_spec.obs_date < datetime(2019, 8, 30):
        delta_hint = _named_gaussian(amplitude=2e-12, mean=4101.7, stddev=20, subscript="1")
    else:
        delta_hint = _named_gaussian(amplitude=3e-12, mean=(4095, 4106), stddev=(1, 7), subscript="2") \
                    + _named_gaussian(amplitude=1e-12, mean=(4095, 4106), stddev=(7, 50), subscript="1")

    # The hints for the He I 4686 line.  Isn't present in the early spectra.
    if unc_spec.obs_date < datetime(2019, 9, 2):
        he4686_hint = None
    elif unc_spec.obs_date < datetime(2019, 9, 5):
        he4686_hint = _named_gaussian(amplitude=4e-12, mean=(4680, 4690), stddev=(1, 5), subscript="2") \
                     + _named_gaussian(amplitude=0.5e-12, mean=(4680, 4690), stddev=(7, 50), subscript="1")
    else:
        he4686_hint = _named_gaussian(amplitude=6e-12, mean=(4680, 4690), stddev=(1, 5), subscript="2") \
                     + _named_gaussian(amplitude=0.2e-12, mean=(4680, 4690), stddev=(7, 50), subscript="1")

    # Now we fit the lines + continuum to the spectrum + uncertainty based on the hints.
    # From the astropy documentation; to get 1/sigma^2 weighting pass in 1/sigma
    weights = np.divide(1, unc_spec.uncertainty.quantity)
    fits = list()
    fits.append(_perform_fit(CompoundModel("+", beta_hint, cont_model, name="H$\\beta$"), unc_spec, weights))
    fits.append(_perform_fit(CompoundModel("+", gamma_hint, cont_model, name="H$\\gamma$"), unc_spec, weights))
    fits.append(_perform_fit(CompoundModel("+", delta_hint, cont_model, name="H$\\delta$"), unc_spec, weights))
    if he4686_hint is not None:
        fits.append(_perform_fit(CompoundModel("+", he4686_hint, cont_model, name="He II (4686)"), unc_spec, weights))
    return fits


@fit_utilities.trace_fitting
def fit_red_arm_spectrum(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    # Derive the uncertainties in the spectrum from the noise. We use this for fitting as it provides weighting.
    unc_spec = spectrum.to_uncertainty_spectrum(Spectrum1DEx.spectral_region_over(6200, 6900, si.AA))

    # Work out the continuum model
    cont_model = _continuum_fit(unc_spec)

    if unc_spec.obs_date < datetime(2019, 8, 29):
        alpha_hint = _named_gaussian(amplitude=8e-12, mean=6562.8, stddev=50, subscript="1")
    elif unc_spec.obs_date < datetime(2019, 9, 5):
        # H-alpha double Gaussian - asymmetric expansion
        alpha_hint = _named_gaussian(amplitude=8e-12, mean=6562.8, stddev=(1, 15), subscript="2") \
                    + _named_gaussian(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="1")
    else:
        alpha_hint = _named_gaussian(amplitude=4e-12, mean=6562.8, stddev=2, subscript="2") \
                    + _named_gaussian(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="1") \

    # Now we fit the lines + continuum to the spectrum + uncertainty based on the hints.
    # From the astropy documentation; to get 1/sigma^2 weighting pass in 1/sigma
    weights = np.divide(1, unc_spec.uncertainty.quantity)
    fits = list()
    fits.append(_perform_fit(CompoundModel("+", alpha_hint, cont_model, "H$\\alpha$"), unc_spec, weights))
    return fits


def _perform_fit(hint: CompoundModel, uncertainty_spectrum, weights) -> CompoundModel:
    fitter = LevMarLSQFitter()
    return fitter(hint, uncertainty_spectrum.wavelength, uncertainty_spectrum.flux, weights=weights)


def _named_gaussian(
        amplitude: Union[float, Tuple[float, float]],
        mean: Union[float, Tuple[float, float]] = None,
        stddev: Union[float, Tuple[float, float]] = None,
        name="fit",
        subscript=None) -> Gaussian1D:
    """
    Initialize a named Gaussian1D model.  The amplitude, mean and stddev arguments will either
    take a single value which will be passed directly to the model or a tuple of two values which
    will be used to set up a bounded argument on the model.  The name a subscript are used to name the model.
    """
    bounds = {}

    if isinstance(amplitude, tuple):
        bounds["amplitude"] = copy(amplitude)
        amplitude = np.mean(amplitude)

    if isinstance(mean, tuple):
        bounds["mean"] = copy(mean)
        mean = np.mean(mean)

    if isinstance(stddev, tuple):
        bounds["stddev"] = copy(stddev)
        stddev = np.mean(stddev)

    if subscript is None or len(subscript) == 0:
        full_name = name
    else:
        full_name = name + f"$_{{{subscript}}}$"
    return Gaussian1D(amplitude=amplitude, mean=mean, stddev=stddev, bounds=bounds, name=full_name)


def _continuum_fit(spectrum: Spectrum1D, name="continuum") -> Polynomial1D:
    """
    Create a fixed, Polynomial1D model for the continuum of the passed spectrum.
    Uses specutils and exclusion regions to fit only to selected regions of the passed spectrum
    """
    # Select the exclusion regions based on whether this is a blue or red arm spectrum
    if min(spectrum.wavelength.value) < 5000:
        exclusion_regions = _b_e_exclusion_regions
    else:
        exclusion_regions = _r_e_exclusion_regions

    # It's a bit of a bodge, but this is the easiest way I could find for selecting/excluding regions for fitting.
    continuum_model = fit_generic_continuum(spectrum,
                                            model=Polynomial1D(degree=2),
                                            exclude_regions=exclusion_regions)

    # Create a new Polynomial1D with the same params (fixed)
    return Polynomial1D(degree=continuum_model.degree,
                        c0=continuum_model.c0, c1=continuum_model.c1, c2=continuum_model.c2,
                        fixed={"c0": True, "c1": True, "c2": True}, name=name)
