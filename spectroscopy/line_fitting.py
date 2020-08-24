import numpy as np
from typing import Dict, List, Tuple, Union
from astropy.units import Quantity
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from astropy.modeling.fitting import LevMarLSQFitter
from specutils import SpectralRegion, Spectrum1D
from specutils.manipulation.extract_spectral_region import *
from specutils.manipulation.estimate_uncertainty import noise_region_uncertainty
from spectroscopy import Spectrum1DEx, fit_utilities


def fit(spectrum: Spectrum1DEx, key: str = None) -> List[CompoundModel]:
    this_module = __import__(__name__)
    method = f"fit_{key}" if key is not None else f"fit_{spectrum.name}"
    func = getattr(this_module, method)
    return func(spectrum)


@fit_utilities.trace_fitting
def fit_b_e_20190828_3(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190828_3(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    hint = CompoundModel("+", _h_alpha_fit(amplitude=8e-12, stddev=50), _continuum_fit(), name="H$\\alpha$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190828_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190828_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    hint = CompoundModel("+", _h_alpha_fit(amplitude=8e-12, stddev=50), _continuum_fit(), name="H$\\alpha$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190830_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190830_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190831_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190831_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190831_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190831_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190901_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190901_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190901_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190901_11(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190902_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190902_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190902_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190902_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190903_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190903_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190903_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190903_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190904_4(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(stddev=(1, 14)), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190904_4(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)
    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=8e-12, stddev=(1, 15), subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6560, 6565), stddev=(30, 60), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190905_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190905_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190905_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190905_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190910_1(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190910_1(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190911_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190911_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190911_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190911_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190913_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190913_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190913_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190913_7(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_b_e_20190915_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 4700, 4900)
    hint = CompoundModel("+", _h_beta_fit(amplitude=2e-12, stddev=22), _continuum_fit(), name="H$\\beta$")
    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


@fit_utilities.trace_fitting
def fit_r_e_20190915_5(spectrum: Spectrum1DEx) -> List[CompoundModel]:
    noise_spectrum = _get_uncertainty_spectrum(spectrum, 6300, 6700)

    # H-alpha double Gaussian - asymmetric expansion
    hint = _h_alpha_fit(amplitude=4e-12, stddev=2, subscript="1") \
           + _h_alpha_fit(amplitude=2e-12, mean=(6569, 6565), stddev=(20, 50), subscript="2") \
           + _continuum_fit()
    hint.name = "H$\\alpha$"

    line_fit = _perform_weighted_fit(hint, noise_spectrum)
    return [line_fit]


def _get_uncertainty_spectrum(spectrum: Spectrum1DEx, lower: float, upper: float):
    noise_region = Spectrum1DEx.spectral_region_over(lower, upper)
    return noise_region_uncertainty(spectrum, noise_region)


def _perform_weighted_fit(hint: CompoundModel, uncertainty_spectrum) -> CompoundModel:
    fitter = LevMarLSQFitter()
    return fitter(hint, uncertainty_spectrum.wavelength, uncertainty_spectrum.flux,
                  weights=np.divide(1, np.power(uncertainty_spectrum.uncertainty.quantity, 2)))


def _continuum_fit(degree=1, name="continuum") -> Polynomial1D:
    return Polynomial1D(degree=degree, name=name, )


def _h_alpha_fit(amplitude: Union[float, Tuple[float, float]] = 5e-12,
                 mean: Union[float, Tuple[float, float]] = 6563,
                 stddev: Union[float, Tuple[float, float]] = None,
                 subscript=None) -> Gaussian1D:
    return _named_gaussian(amplitude, mean, stddev, subscript=subscript)


def _h_beta_fit(amplitude: Union[float, Tuple[float, float]] = 2e-12,
                mean: Union[float, Tuple[float, float]] = 4861,
                stddev: Union[float, Tuple[float, float]] = None,
                subscript=None) -> Gaussian1D:
    return _named_gaussian(amplitude, mean, stddev, subscript=subscript)


def _named_gaussian(
        amplitude: Union[float, Tuple[float, float]],
        mean: Union[float, Tuple[float, float]] = None,
        stddev: Union[float, Tuple[float, float]] = None,
        name="fit",
        subscript=None) -> Gaussian1D:
    bounds = {}

    if isinstance(amplitude, tuple):
        bounds["amplitude"] = amplitude
        amplitude = np.mean(amplitude)

    if isinstance(mean, tuple):
        bounds["stddev"] = mean
        mean = np.mean(mean)

    if isinstance(stddev, tuple):
        bounds["stddev"] = stddev
        stddev = np.mean(stddev)

    if subscript is None or len(subscript) == 0:
        full_name = name
    else:
        full_name = name + f"$_{{{subscript}}}$"
    return Gaussian1D(amplitude=amplitude, mean=mean, stddev=stddev, bounds=bounds, name=full_name)
