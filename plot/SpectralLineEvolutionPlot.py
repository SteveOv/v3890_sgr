from typing import Dict, List, Tuple
import numpy as np
from matplotlib.axes import Axes
from plot import BasePlot
from spectroscopy import fit_utilities as fu
from cycler import cycler


class SpectralLineEvolutionPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # refined defaults for BasePlot
        self._default_x_label = "Velocity [km s$^{{-1}}$]"
        self._default_x_lim = (-6000, 6000)                     # km / s
        self._default_x_ticks = [-5000, -2500, 0, 2500, 5000]   # km / s
        self._default_x_tick_labels = self._default_x_ticks
        self._default_y_label = "Flux density"

        # Extending the properties of BasePlot
        self._default_y_lim = (-0.1, 1.0)
        self._default_y_ticks = [0, 0.5, 1.0]
        self._default_y_shift = 0

        self._default_lambda_0 = 6562.79
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
    def y_shift(self) -> float:
        return self._param("y_shift", self._default_y_shift)

    @property
    def y_tick_labels(self) -> List[str]:
        return self._param("y_tick_labels", self._default_y_ticks)

    @property
    def lambda_0(self) -> float:
        return self._param("lambda_0", self._default_lambda_0)

    def _configure_ax(self, ax: Axes, **kwargs):
        super()._configure_ax(ax, **kwargs)

        # The underlying data is the wavelength/flux of the region of the spectra centred on lambda_0.
        # However, the limits, ticks and labels are specified in km / s so conversions are required.
        limit_dispersions = list()
        for limit in self.x_lim:
            limit_dispersions.append(fu.calculate_sigma_from_velocity(self.lambda_0, limit * 1000))
        ax.set_xlim(np.add(limit_dispersions, self.lambda_0))

        tick_dispersions = list()
        for x_tick in self.x_ticks:
            tick_dispersions.append(fu.calculate_sigma_from_velocity(self.lambda_0, x_tick * 1000))

        ax.set_xticks(np.add(tick_dispersions, self.lambda_0), minor=False)
        ax.set_xticklabels(self.x_tick_labels, minor=False)

        ax.set(ylim=self.y_lim)
        ax.set_yticks(self.y_ticks, minor=False)
        ax.set_yticklabels(self.y_tick_labels, minor=False)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        spectra = kwargs["spectra"]
        ix = 0

        # We'll cycle the colors.
        if self.lambda_0 < 5000:
            ax.set_prop_cycle(cycler(color=["b", "tab:blue", "dodgerblue", "lightskyblue"]))
        else:
            ax.set_prop_cycle(cycler(color=["tab:red", "r", "orangered", "tomato"]))

        for spec_key in reversed(list(spectra.keys())):
            spectrum = spectra[spec_key]
            flux = spectrum.flux if self.y_shift == 0 else np.add(spectrum.flux, self.y_shift * ix * spectrum.flux.unit)
            label = spec_key
            ax.plot(spectrum.spectral_axis, flux, label=label, linestyle="-", linewidth=0.25)
            ix += 1
        return

