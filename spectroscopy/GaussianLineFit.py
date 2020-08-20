from typing import Dict
import numpy as np
from matplotlib.axes import Axes
from astropy.units import Quantity
from astropy.modeling import CompoundModel
from astropy.modeling.models import Gaussian1D, Polynomial1D
from astropy.modeling.fitting import LevMarLSQFitter
from specutils import SpectralRegion
from specutils.manipulation import *
from spectroscopy import Spectrum1DEx, GaussianLineFit


class GaussianLineFit:
    """
    This represents the fitting of a single spectral line.
    TODO: Doesn't 'fit' into the Fit/FitSet model I created for photometry although I've tried to keep things similar.  Rework the 2 models into 1.
    """

    _resolving_power = {
        "blue-high": 5500,
        "red-high": 5300
    }

    def __init__(self, id: int, range_from, range_to, **kwargs):
        self.__id = id
        self._range_from = range_from
        self._range_to = range_to
        self._model = kwargs["model"] if "model" in kwargs else None
        self._color = kwargs["color"] if "color" in kwargs else "m"
        return

    @property
    def id(self) -> int:
        return self.__id

    @property
    def label(self):
        return self._model.name if self._model is not None else None

    @property
    def color(self):
        return self._color

    @property
    def has_fit(self) -> bool:
        return self._model is not None

    @property
    def amplitude(self):
        return self.model.amplitude.quantity if self.model is not None else None

    @property
    def mean(self):
        return self.model.mean.quantity if self.model is not None else None

    @property
    def stddev(self):
        return self.model.stddev.quantity if self.model is not None else None

    @property
    def fwhm(self):
        return self.model.fwhm if self.model is not None else None

    @property
    def model(self) -> Gaussian1D:
        if self._model is not None:
            if isinstance(self._model, CompoundModel):
                value = self._model["line"]
            else:
                value = self._model
        else:
            value = None
        return value

    @property
    def velocity_dispersion(self):
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
        r = self._resolving_power["blue-high"] if self.mean.value < 5500 else self._resolving_power["red-high"]
        beta_spec = np.sqrt(self.fwhm**2 - (self.mean / r)**2)

        # This is the FWHM corrected for the spectrograph's LSF.  It's related to the velocity dispersion through
        sigma = beta_spec / 2.355  # 2 sqrt(2 ln2)
        v = (sigma / self.mean) * Quantity(2.998e5, unit="km/s")
        return v

    @classmethod
    def fit_to_data(cls, id: int, spectrum: Spectrum1DEx, noise_region: SpectralRegion,
                    hint: Dict, label: str = None, **kwargs):
        """
        Fit a Gaussian model to the spectrum based on the passed hint.  The noise_region indicate a
        region of the spectrum to sample for noise uncertainty.  The hint must include values which estimate
        the fit sought, hint keys are;
            amplitude
            mean
            stddev
        A combination model of a Gaussian fit and a polynomial continuum will be created.  The properties
        of the result will reflect the Gaussian relative to the continuum.
        """

        # Allow an estimation of the uncertainty due to noise.
        if noise_region is None:
            noise_region = SpectralRegion.from_center(center=Quantity(hint["mean"], spectrum.wavelength.unit),
                                                      width=Quantity(hint["stddev"] * 10, spectrum.wavelength.unit))

        noise_spectrum = noise_region_uncertainty(spectrum, noise_region)
        model = CompoundModel("+", Gaussian1D(**hint, name="line"), Polynomial1D(degree=1, name="cont"), name=label)
        fitter = LevMarLSQFitter()
        gaussian_fit = fitter(model,
                              noise_spectrum.wavelength,
                              noise_spectrum.flux,
                              weights=np.divide(1, np.power(noise_spectrum.uncertainty.quantity, 2)))

        print(gaussian_fit)
        range_from = spectrum.min_wavelength
        range_to = spectrum.max_wavelength

        fit = GaussianLineFit(id, range_from, range_to, model=gaussian_fit, **kwargs)
        return fit

    def draw_on_ax(self, ax: Axes, line_width: float = 0.5, label: str = None,
                   y_shift: float = 0, annotate: bool = True):
        """
        Gets the fit to draw itself onto the passed matplotlib ax and then to annotate
        """
        # Generate the plot data points from the model.
        x_plot = Quantity(np.linspace(self._range_from.value, self._range_to.value, 1000), unit=self._range_from.unit)
        y_plot = self._model(x_plot)

        ax.plot(x_plot, np.add(y_plot, y_shift), "-", color=self.color, linewidth=line_width, alpha=0.5, zorder=2)

        if annotate and self._model is not None:
            if label is None:
                label = self.label
            text = \
                f"{label}\n$\\mu$={self.mean:.1f}\nFWHM={self.fwhm:.2f}\n$v_{{\\sigma}}$={self.velocity_dispersion:.1f}"

            # Have to take the units off for this, otherwise you get an UnitConversionError when saving the plot
            peak_position = (self.mean.value, max(y_plot).value)
            ax.annotate(text, xycoords="data", xy=peak_position, textcoords="offset pixels", xytext=(20, 0),
                        color=self.color, fontsize="x-small")
        return
