import math
import numpy as np
from matplotlib.axes import Axes
from astropy import units as u
from astropy.units import Quantity
from astropy.modeling import Model
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from astropy.modeling.fitting import LevMarLSQFitter
from specutils import SpectralRegion
from specutils.manipulation.estimate_uncertainty import noise_region_uncertainty
from spectroscopy import Spectrum1DEx

_frodo_spec_resolving_power = {
    "blue-high": 5500,
    "red-high": 5300
}


def calculate_velocity_dispersion(fit: Gaussian1D) -> Quantity:
    """
    Get the velocity dispersion of this fit, based on the line's Gaussian dispersion and the LSF of the instrument.
    """
    # TODO: rework this so it's based directly on the dispersion and avoid the FWHM/2.355 step?
    # The line width is the product of convolving the line spread function (LSF) of the spectrograph with
    # the emission line.  Taking both to be Gaussian, we have
    #   G_obs(x) = 1/(B_obs*sqrt(pi)) exp(-x^2/B_obs^2) where beta_obs^2 = beta_LSF^2 + beta_spec^2
    # we take beta_obs = FWHM of the observed line
    # and we can work out beta_LSF = lambda_0/R
    # therefore B_spec = sqrt( beta_obs^2 - beta_LSF^2 )
    #
    mu = fit.mean.quantity
    fwhm = fit.fwhm

    r = _frodo_spec_resolving_power["blue-high"] if mu.value < 5500 else _frodo_spec_resolving_power["red-high"]
    beta_spec = np.sqrt(fwhm**2 - (mu / r)**2)

    # This is the FWHM corrected for the spectrograph's LSF.  It's related to the velocity dispersion through
    sigma = beta_spec / 2.355  # 2 sqrt(2 ln2)
    v = (sigma / mu) * Quantity(2.998e5, unit="km/s")
    return v


def calculate_flux(fit: Gaussian1D) -> Quantity:
    """
    Calculate the flux of a Gaussian fit.  flux = A * sigma * sqrt(2*pi)
    """
    amplitude = fit.amplitude.quantity
    sigma = fit.stddev.quantity
    return amplitude * sigma * np.sqrt(2 * math.pi)


def draw_fit_on_ax(ax: Axes, spectrum: Spectrum1DEx, fit: Model, annotate: bool = True,
                   color: str = "m", line_width: float = 0.5, y_shift: float = 0):
    draw_fit_on_ax_over_range(ax, spectrum.min_wavelength, spectrum.max_wavelength, fit, annotate=annotate,
                              color=color, line_width=line_width, y_shift=y_shift)
    return


def draw_fit_on_ax_over_range(ax: Axes, start: Quantity, end: Quantity, fit: Model, annotate: bool = True,
                              color: str = "m", line_width: float = 0.5, y_shift: float = 0):
    x_plot = Quantity(np.linspace(start.value, end.value, 1000), start.unit)
    y_plot = fit(x_plot)

    # Draw the model
    ax.plot(x_plot, np.add(y_plot, y_shift), "-", color=color, linewidth=line_width, alpha=0.5, zorder=2)

    if annotate:
        if isinstance(fit, CompoundModel):
            text = describe_compound_fit(fit, for_matplotlib=True, include_amplitude=False, include_flux=False)
        elif isinstance(fit, Gaussian1D):
            text = describe_gaussian_fit(fit, for_matplotlib=True, include_amplitude=True, include_flux=False)
        else:
            text = f"Cannot yet describe {fit.__class__.__name__}"

        # Have to take the units off for this, otherwise you get an UnitConversionError when saving the plot
        peak_position = (fit.mean_0.value, max(y_plot).value)
        ax.annotate(text, xycoords="data", xy=peak_position, textcoords="offset pixels", xytext=(20, 0),
                    color=color, fontsize="x-small")
    return


def describe_compound_fit(fit: CompoundModel, for_matplotlib: bool = False, **kwargs):
    text = f"{fit.name}"
    for sub in fit:
        if isinstance(sub, Gaussian1D):
            text += ("\n\t" if not for_matplotlib else "\n") + describe_gaussian_fit(sub, for_matplotlib, **kwargs)
    return text


def describe_gaussian_fit(fit: Gaussian1D, for_matplotlib: bool = False, include_amplitude: bool = True,
                          include_flux: bool = True) -> str:
    amplitude = fit.amplitude.quantity
    mu = fit.mean.quantity
    sigma = fit.stddev.quantity

    v_sigma = calculate_velocity_dispersion(fit)
    text = f"{fit.name}. " if fit.name is not None and len(fit.name) > 0 else ""
    if for_matplotlib:
        text += f"$\\mu$={mu.value:.1f} {mu.unit:latex_inline}, " \
                f"$v_{{\\sigma}}$={v_sigma.value:.1f} {v_sigma.unit:latex_inline}"
        if include_amplitude:
            text += f", A={amplitude.value:.1e} {amplitude.unit:latex_inline}"
        if include_flux:
            flux = calculate_flux(fit)
            text += f", flux=${flux.value:.2e}$ {flux.unit:latex_inline}"
    else:
        text += f"mu={mu:.2f}, sigma={sigma:.2f}, v_sigma={v_sigma}"
        if include_amplitude:
            text += f", A={amplitude:.2e}"
        if include_flux:
            flux = calculate_flux(fit)
            text += f", flux={flux:.3e}"
    return text
