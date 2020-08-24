from typing import Dict, List, Tuple
import numpy as np
from matplotlib.axes import Axes
from astropy.units import Quantity, si
from plot import BasePlot
from spectroscopy import fit_utilities as fu


class SpectralLineEvolutionPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # refined defaults for BasePlot
        self._default_x_label = "Velocity [km s$^{{-1}}$]"
        self._default_x_lim = (-6000, 6000)
        self._default_x_ticks = [-5000, 0, 5000]
        self._default_x_tick_labels = self._default_x_ticks
        self._default_y_label = "Arbitrary flux"

        # Extending the properties of BasePlot
        self._default_y_lim = (-0.1, 1.0)
        self._default_y_ticks = [0, 0.5, 1.0]

        self._default_lambda_zero = 6562.79
        self._default_normalize = False
        return

    @property
    def x_tick_labels(self):
        return self._param("x_tick_labels", self._default_x_tick_labels)

    @property
    def y_lim(self) -> Tuple[float]:
        return self._param("y_lim", self._default_y_lim)

    @property
    def y_ticks(self) -> List[float]:
        return self._param("y_ticks", self._default_y_ticks)

    @property
    def y_tick_labels(self) -> List[str]:
        return self._param("y_tick_labels", self._default_y_ticks)

    @property
    def lambda_zero(self) -> float:
        return self._param("lambda_zero", self._default_lambda_zero)

    @property
    def normalize(self) -> bool:
        return self._param("normalize", self._default_normalize)

    def _configure_ax(self, ax: Axes, **kwargs):

        # The underlying data on the x-axis is the dispersion/stddev of the fit.
        # It's labelled as km/s so we need to convert some given values.
        dispersions = (
            fu.calculate_sigma_from_velocity(self.lambda_zero, -6000e3),
            fu.calculate_sigma_from_velocity(self.lambda_zero, -5000e3),
            fu.calculate_sigma_from_velocity(self.lambda_zero, -2500e3),
            0,
            fu.calculate_sigma_from_velocity(self.lambda_zero, 2500e3),
            fu.calculate_sigma_from_velocity(self.lambda_zero, 5000e3),
            fu.calculate_sigma_from_velocity(self.lambda_zero, 6000e3)
        )

        self._default_x_lim = (self.lambda_zero + dispersions[0], self.lambda_zero + dispersions[6])
        self._default_x_ticks = np.add(self.lambda_zero, dispersions[1:6])
        self._default_x_tick_labels = ["-5000", "-2500", "0", "2500", "5000"]

        if self.normalize:
            self._default_y_label = "Arbitrary flux"
        else:
            self._default_y_label = f"Flux density"

        super()._configure_ax(ax, **kwargs)

        if self.normalize:
            ax.set(ylim=(-0.1, 1.1))
            ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0], minor=False)
            ax.set_yticklabels([0], minor=False)
        else:
            ax.set(ylim=self.y_lim)
            ax.set_yticks(self.y_ticks, minor=False)
            ax.set_yticklabels(self.y_tick_labels, minor=False)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        spectra = kwargs["spectra"]
        line_fits = kwargs["line_fits"]
        for spec_key, spectrum in spectra.items():
            flux = spectrum.flux
            if spec_key in line_fits:
                # Normalize the spectral data by scaling to the line's fit (or maximum flux) and remove the continuum.
                fits = line_fits[spec_key]
                for model in fits:
                    if model.name == "H$\\alpha$":
                        continuum = model(spectrum.spectral_axis)
                        if self.normalize:
                            flux = np.subtract(flux, continuum)
                            flux = np.divide(flux, max(flux))
                        break

            label = spec_key
            color = "g"
            ax.plot(spectrum.spectral_axis, flux, label=label, color=color, linestyle="-", linewidth=0.25)
        return

