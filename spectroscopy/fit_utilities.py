import math
import functools
import numpy as np
from typing import Union, List
from matplotlib.axes import Axes
from astropy import units as u
from astropy.units import Quantity
from astropy.modeling import Model
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from spectroscopy import Spectrum1DEx

_fit_colors = ["m", "royalblue", "darkmagenta", "cyan", "violet", "mediumpurple"]

_frodo_spec_resolving_power = {
    "blue-high": 5500,
    "red-high": 5300
}

c = 2.998e8 * u.m / u.s


def calculate_velocity_from_sigma(lambda_0: Union[float, Quantity], sigma: Union[float, Quantity]) \
        -> Union[float, Quantity]:
    v_sigma = (sigma / lambda_0) * (c if isinstance(lambda_0, Quantity) and isinstance(sigma, Quantity) else c.value)
    return v_sigma


def calculate_sigma_from_velocity(lambda_0: Union[float, Quantity], velocity_sigma: Union[float, Quantity]) \
        -> Union[float, Quantity]:
    sigma = (velocity_sigma * lambda_0) / (c if isinstance(lambda_0, Quantity) and isinstance(velocity_sigma, Quantity) else c.value)
    return sigma


def calculate_flux(fit: Gaussian1D) -> Quantity:
    """
    Calculate the flux of a Gaussian fit.  flux = A * sigma * sqrt(2*pi)
    """
    amplitude = fit.amplitude.quantity
    sigma = fit.stddev.quantity
    return amplitude * sigma * np.sqrt(2 * math.pi)


def draw_fit_on_ax(ax: Axes, spectrum: Spectrum1DEx, fit: Model, annotate: bool = True,
                   color: str = "m", line_width: float = 0.5, y_shift: float = 0, split=False):
    draw_fit_on_ax_over_range(ax, spectrum.min_wavelength, spectrum.max_wavelength, fit, annotate=annotate,
                              color=color, line_width=line_width, y_shift=y_shift, split=split)
    return


def draw_fit_on_ax_over_range(ax: Axes, start: Quantity, end: Quantity, fit: Model, annotate: bool = True,
                              color: str = "m", line_width: float = 0.5, y_shift: float = 0, split=False):
    x_plot = Quantity(np.linspace(start.value, end.value, 1000), start.unit)

    if not split or not isinstance(fit, CompoundModel):
        # Draw the whole model
        y_plot = fit(x_plot)
        ax.plot(x_plot, np.add(y_plot, y_shift), "-",
                color=_fit_colors[0], linewidth=line_width, alpha=0.5, zorder=2)
    else:
        # Draw the individual elements (except continuum)
        color_ix = 0
        for sub in fit:
            if isinstance(sub, Polynomial1D) and "cont" in sub.name:
                # It's the continuum.  Leave it.
                pass
            else:
                y_plot = sub(x_plot)
                ax.plot(x_plot, np.add(y_plot, y_shift), "-",
                        color=_fit_colors[color_ix], linewidth=line_width, alpha=0.5, zorder=2)
                color_ix += 1

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


def trace_fitting(func, show_parameters=True):
    """
    Decorator for fitting functions (input Spectrum1DEx, returns CompoundModel, GaussianModel or list of)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fit_models = func(*args, **kwargs)

        if show_parameters:
            spectrum = args[0]
            desc = describe_fits(fit_models, for_matplotlib=False, include_amplitude=True, include_flux=True)
            print(f"{func.__name__}({spectrum.name}): " + desc)
        return fit_models
    return wrapper


def describe_fits(fit_model: Union[Model, List[Model]], for_matplotlib: bool = False, **kwargs) -> str:
    """
    Write text for tracing or plotting to matplotlib text/annotation describing the fits
    """
    line_start = "\n" if for_matplotlib else "\n\t"
    if isinstance(fit_model, CompoundModel):
        desc = line_start + describe_compound_fit(fit_model, for_matplotlib=for_matplotlib, **kwargs)
    elif isinstance(fit_model, Gaussian1D):
        desc = line_start + describe_gaussian_fit(fit_model, for_matplotlib=for_matplotlib, **kwargs)
    elif isinstance(fit_model, Model):
        desc = line_start + f"{fit_model}"
    else:
        # assume a list thereof
        desc = ""
        for fit in fit_model:
            desc += describe_fits(fit, for_matplotlib=for_matplotlib, **kwargs)
    return desc


def describe_compound_fit(fit: CompoundModel, for_matplotlib: bool = False, **kwargs):
    """
    Write text for tracing or plotting to matplotlib text/annotation describing the compound fit
    """
    text = f"{fit.name}"
    for sub in fit:
        if isinstance(sub, Gaussian1D):
            text += ("\n\t\t" if not for_matplotlib else "\n") + describe_gaussian_fit(sub, for_matplotlib, **kwargs)
    return text


def describe_gaussian_fit(fit: Gaussian1D, for_matplotlib: bool = False, include_amplitude: bool = True,
                          include_flux: bool = True) -> str:
    """
    Write text for tracing or plotting to matplotlib text/annotation describing the Gaussian fit
    """
    amplitude = fit.amplitude.quantity
    mu = fit.mean.quantity
    sigma = fit.stddev.quantity

    v_sigma = calculate_velocity_from_sigma(lambda_0=mu, sigma=sigma).to("km / s")
    text = f"{fit.name}: " if fit.name is not None and len(fit.name) > 0 else ""
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
