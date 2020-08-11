from plot.BasePlot import *
from data.spectrum import *


class SpectrumPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 1
        return

    def _configure_ax(self, ax: Axes, **kwargs):
        # Get the spectra - we'll base the configuration on the data
        spectra = kwargs["spectra"]
        if isinstance(spectra, Spectrum1DEx):
            spectra = [spectra]

        # Now we can set the defaults for labels and axes based on the data
        self._default_y_label = f"Arbitrary flux"
        self._default_x_label = f"Wavelength [{spectra[0].wavelength.unit}]"

        # X Ticks every 500 A
        min_lambda = min(s.min_wavelength.value for s in spectra) - 100
        max_lambda = max(s.max_wavelength.value for s in spectra) + 100
        self._default_x_lim = (min_lambda, max_lambda)
        x_ticks_delta = 500
        first_tick = round(min_lambda / x_ticks_delta) * x_ticks_delta
        self._default_x_ticks = np.arange(first_tick, max_lambda, x_ticks_delta, dtype=int)

        # Y tick only on the zero line
        ax.set_yticks([0], minor=False)
        ax.set_yticklabels([], minor=False)

        super()._configure_ax(ax, **kwargs)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        The method, to be overridden by subclasses, for plotting their data to the passes Axes
        """
        spectra = kwargs["spectra"]
        if isinstance(spectra, Spectrum1DEx):
            spectra = [spectra]

        for spectrum in spectra:
            self._draw_spectrum(ax, spectrum)
        return

    def _draw_spectrum(self, ax: Axes, spectrum: Spectrum1DEx):
        is_blue = min(spectrum.spectral_axis.value) < 5000
        label = "Blue arm" if is_blue else "Red arm"
        color = "b" if is_blue else "r"
        ax.plot(spectrum.spectral_axis, spectrum.flux, label=label, color=color, linestyle="-", linewidth=0.25)
        return
