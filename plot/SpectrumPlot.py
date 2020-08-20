from typing import Tuple
from plot.BasePlot import *
from spectroscopy import *


class SpectrumPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 1

        self._default_show_data = True
        self._default_show_line_fits = True
        self._default_show_spectral_lines = True

        self._default_y_lim = None
        self._default_y_ticks = [0]
        self._default_y_tick_labels = []
        return

    @property
    def show_data(self) -> bool:
        return self._param("show_data", self._default_show_data)

    @property
    def show_line_fits(self) -> bool:
        return self._param("show_fits", self._default_show_line_fits)

    @property
    def show_spectral_lines(self) -> bool:
        return self._param("show_spectral_lines", self._default_show_spectral_lines)

    @property
    def y_lim(self):
        return self._param("y_lim", self._default_y_lim)

    @property
    def y_ticks(self):
        return self._param("y_ticks", self._default_y_ticks)

    @property
    def y_tick_labels(self):
        return self._param("y_tick_labels", self._default_y_tick_labels)

    def _configure_ax(self, ax: Axes, **kwargs):
        # Get the spectra - we'll base the configuration on the data
        spectra, _, _ = self.__class__._extract_payload(kwargs)

        # Now we can set the defaults for labels and axes based on the data
        self._default_y_label = f"Flux [{spectra[0].flux.unit:latex_inline}]"
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

        # Base behaviour has y-axis "dynamic" based on the data.  Keep that behaviour unless explicit limits specified.
        if self.y_lim is not None:
            ax.set_ylim(self.y_lim)

        # Override the ticks though; Y tick only on the zero line
        ax.set_yticks(self.y_ticks, minor=False)
        ax.set_yticklabels(self.y_tick_labels, minor=False)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override from super(), for plotting their data to the passed Axes
        """
        spectra, line_fits, spectral_lines = self.__class__._extract_payload(kwargs)

        if self.show_data:
            self._draw_spectra(ax, spectra)

        if self.show_line_fits and line_fits is not None:
            self._draw_fitted_lines(ax, line_fits)

        if self.show_spectral_lines:
            self._draw_spectral_lines(ax, spectral_lines)
        return

    def _draw_spectra(self, ax: Axes, spectra: Union[Spectrum1DEx, List[Spectrum1DEx]]):
        if spectra is not None:
            if isinstance(spectra, Spectrum1DEx):
                spectra = [spectra]

        for spectrum in spectra:
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

    def _draw_fitted_lines(self, ax: Axes, line_fits: Union[GaussianLineFitSet, List[GaussianLineFitSet]]):
        if self.show_line_fits and line_fits is not None and len(line_fits) > 0:
            if isinstance(line_fits, GaussianLineFitSet):
                self._draw_fitted_lines(ax, [line_fits])
            else:
                for line_fit in line_fits:
                    line_fit.draw_on_ax(ax, annotate=True)
        return

    @classmethod
    def _extract_payload(cls, kwargs) \
            -> Tuple[Union[Spectrum1DEx, List[Spectrum1DEx]], Union[GaussianLineFitSet, List[GaussianLineFitSet]], Dict]:
        spectra = kwargs["spectra"] if "spectra" in kwargs else None
        if spectra is not None and isinstance(spectra, Spectrum1DEx):
            spectra = [spectra]

        spectral_lines = kwargs["spectral_lines"] if "spectral_lines" in kwargs else None

        line_fits = kwargs["line_fits"] if "line_fits" in kwargs else None
        return spectra, line_fits, spectral_lines
