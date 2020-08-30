from typing import Tuple
import numpy as np
from plot.BasePlot import *
from spectroscopy import *


class SpectrumPlot(BasePlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 1

        self._default_show_legend = False
        self._default_show_data = True
        self._default_show_line_fits = False
        self._default_show_line_labels = True

        self._default_y_lim = None
        self._default_y_ticks = [0]
        self._default_y_tick_labels = []

        self._default_line_colors = "k"
        return

    @property
    def show_data(self) -> bool:
        return self._param("show_data", self._default_show_data)

    @property
    def show_line_fits(self) -> bool:
        return self._param("show_fits", self._default_show_line_fits)

    @property
    def show_line_labels(self) -> bool:
        return self._param("show_line_labels", self._default_show_line_labels)

    @property
    def y_lim(self):
        return self._param("y_lim", self._default_y_lim)

    @property
    def y_ticks(self):
        return self._param("y_ticks", self._default_y_ticks)

    @property
    def y_tick_labels(self):
        return self._param("y_tick_labels", self._default_y_tick_labels)

    @property
    def line_colors(self) -> Union[str, Dict[str, str]]:
        """
        Either a single color for all spectral lines, or a dictionary keyed on line set name.
        """
        return self._param("line_colors", self._default_line_colors)

    def _configure_ax(self, ax: Axes, **kwargs):
        # Get the spectra - we'll base the configuration on the data
        spectra, _, _ = self.__class__._extract_payload(kwargs)

        # Now we can set the defaults for labels and axes based on the data
        s1 = spectra[next(iter(spectra))]
        self._default_y_label = f"Flux density [{s1.flux.unit:latex_inline}]"
        self._default_x_label = f"Wavelength [{s1.wavelength.unit:latex_inline}]"

        min_lambda = min(s.min_wavelength.value for k, s in spectra.items()) - 100
        max_lambda = max(s.max_wavelength.value for k, s in spectra.items()) + 100
        self._default_x_lim = (min_lambda, max_lambda)

        # Major X Ticks every 500 A
        def _calculate_x_ticks(x_min, x_max, x_ticks_delta):
            first_tick = round(x_min / x_ticks_delta) * x_ticks_delta
            return np.arange(first_tick, x_max, x_ticks_delta, dtype=int)
        self._default_x_ticks = _calculate_x_ticks(min_lambda, max_lambda, 500)

        # Do the basic config now we have defined the default behaviour
        super()._configure_ax(ax, **kwargs)

        # Minor x ticks every 100 A
        ax.set_xticks(_calculate_x_ticks(min_lambda, max_lambda, 100), minor=True)

        # Base behaviour has y-axis "dynamic" based on the data.  Keep that behaviour unless explicit limits specified.
        if self.y_lim is not None:
            ax.set_ylim(self.y_lim)

        # Override the ticks though; Y tick only on the zero line
        ax.set_yticks(self.y_ticks, minor=False)
        ax.set_yticklabels(self.y_tick_labels, minor=False)
        ax.grid(which="major", axis="x")
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override from super(), for plotting their data to the passed Axes
        """
        spectra, line_fits, spectral_line_labels = self.__class__._extract_payload(kwargs)

        if self.show_data:
            self._draw_spectra(ax, spectra)

        if self.show_line_fits:
            self._draw_fitted_lines(ax, spectra, line_fits)

        if self.show_line_labels:
            self._draw_spectral_line_labels(ax, spectral_line_labels)
        return

    def _draw_spectra(self, ax: Axes, spectra: Dict[str, Spectrum1DEx]):
        if self.show_data and spectra is not None:
            for spec_key, spectrum in spectra.items():
                color = "b" if spectrum.is_blue else "r"
                label = "Blue arm" if spectrum.is_blue else "Red arm"
                ax.plot(spectrum.spectral_axis, spectrum.flux, label=label, color=color, linestyle="-", linewidth=0.10)
        return

    def _draw_fitted_lines(self, ax: Axes, spectra: Dict[str, Spectrum1DEx], line_fits: Dict[str, List[Model]]):
        if self.show_line_fits and line_fits is not None and len(line_fits) > 0:
            for fit_key, line_fit_list in line_fits.items():
                spectrum = spectra[fit_key] if fit_key in spectra else None
                for line_fit in line_fit_list:
                    fit_utilities.draw_fit_on_ax(ax, spectrum, line_fit, annotate=False)
        return

    def _draw_spectral_line_labels(self, ax: Axes, spectral_line_labels: List[Dict]):
        """
        Will plot spectral line labels with vertical dashed lines at the appropriate wavelengths.
        The spectral_line_labels arg is an array of dictionaries.  Each dictionary holds the labels for a row
        with items keyed on wavelength (str) with the value the label (allows for non-unique labels for doublets).
        As each row is plotted the labels are moved downwards to aid legibility/avoid clashes/overwriting.
        """
        if self.show_line_labels and spectral_line_labels is not None and len(spectral_line_labels) > 0:
            ix = 0
            label_offset = 0.15
            color = self._default_line_colors
            for labels_row in spectral_line_labels:
                x_pos = list()
                labels = list()
                for wavelength, label in labels_row.items():
                    wl = float(wavelength)
                    x_pos.append(wl)
                    if "%d" in label:
                        labels.append(label % wl)
                    elif "%s" in label:
                        labels.append(label % wavelength)
                    else:
                        labels.append(label)

                self._draw_vertical_lines(ax, x=x_pos, text=labels, color=color, text_size="3.0", line_width=0.2,
                                          v_align="bottom", text_top=True, text_offset=0.10 + (label_offset * ix))
                ix += 1
        return

    @classmethod
    def _extract_payload(cls, kwargs) \
            -> Tuple[Dict[str, Spectrum1DEx], Dict[str, List[Model]], List[Dict]]:
        spectra = kwargs["spectra"] if "spectra" in kwargs else None

        line_fits = kwargs["line_fits"] if "line_fits" in kwargs else None

        spectral_line_labels = kwargs["spectral_line_labels"] if "spectral_line_labels" in kwargs else None
        return spectra, line_fits, spectral_line_labels
