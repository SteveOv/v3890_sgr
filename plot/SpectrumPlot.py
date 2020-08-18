from plot.BasePlot import *
from data.spectrum import *


class SpectrumPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 1

        self._default_show_spectral_lines = True
        self._default_y_lim = (-1, 100)
        return

    @property
    def show_spectral_lines(self) -> bool:
        return self._param("show_spectral_lines", self._default_show_spectral_lines)

    @property
    def y_lim(self):
        return self._param("y_lim", self._default_y_lim)

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

        # Do the basic config now we have defined the default behaviour
        super()._configure_ax(ax, **kwargs)

        # Basic config leaves y-axis dynamic.  Override this here; Y tick only on the zero line and a range limit
        ax.set_ylim(self.y_lim)
        ax.set_yticks([0], minor=False)
        ax.set_yticklabels([], minor=False)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override from super(), for plotting their data to the passes Axes
        """
        spectra = kwargs["spectra"]
        if isinstance(spectra, Spectrum1DEx):
            spectra = [spectra]

        for spectrum in spectra:
            self._draw_spectrum(ax, spectrum)

        if self.show_spectral_lines and "spectral_lines" in kwargs:
            spectral_lines = kwargs["spectral_lines"]
            self._draw_spectral_lines(ax, spectral_lines)
        return

    def _draw_spectrum(self, ax: Axes, spectrum: Spectrum1DEx):
        color = "b" if spectrum.is_blue else "r"
        label = "Blue arm" if spectrum.is_blue else "Red arm"
        if spectrum.flux_scale_factor != 1:
            label += f" (scaled by {spectrum.flux_scale_factor})"
        ax.plot(spectrum.spectral_axis, spectrum.flux, label=label, color=color, linestyle="-", linewidth=0.25)
        return

    def _draw_spectral_lines(self, ax: Axes, spectral_lines):
        if spectral_lines is not None and len(spectral_lines) > 0:
            # Replace the minor x-axis ticks with the epochs specified.
            ax.set_xticks(list(spectral_lines.values()), minor=True)
            ax.set_xticklabels(list(spectral_lines.keys()), minor=True)

            # Labels, if shown, are rotated 90deg and within the axis.
            ax.tick_params(which='minor', axis='x', direction='inout', pad=-35, labelsize='x-small',
                           labelcolor='k', top=True, bottom=True, labeltop=False, labelbottom=True,
                           labelrotation=90)
            ax.grid(which='minor', linestyle=':', linewidth=self._line_width, alpha=0.3)
        return
