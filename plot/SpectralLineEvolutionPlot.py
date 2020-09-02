from plot.SpectralPlot import *
from spectroscopy import fit_utilities as fu
from utility import timing as tm
from cycler import cycler


class SpectralLineEvolutionPlot(SpectralPlot):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # refined defaults for BasePlot
        self._default_show_legend = False
        self._default_x_label = "Velocity [km s$^{{-1}}$]"
        self._default_x_lim = (-6000, 6000)                     # km / s
        self._default_x_ticks = [-5000, -2500, 0, 2500, 5000]   # km / s
        self._default_x_tick_labels = self._default_x_ticks

        self._default_y_label = "Flux density [$10^{-12}$ $\\mathrm{erg\\,\\mathring{A}^{-1}\\,s^{-1}\\,cm^{-2}}$]"

        self._default_y_shift = 0
        self._default_y_shift_type = "linear"

        self._default_lambda_0 = 6562.79
        self._default_fit_name = "H$\\alpha$"
        self._default_subtract_continuum = False
        return

    @property
    def x_tick_labels(self):
        return self._param("x_tick_labels", self._default_x_tick_labels)

    @property
    def y_shift(self) -> float:
        return self._param("y_shift", self._default_y_shift)

    @property
    def y_shift_type(self) -> str:
        return self._param("y_shift_type", self._default_y_shift_type)

    @property
    def y_shift_by_delta_t(self) -> bool:
        return self.y_shift_type.casefold() in ["delta_t", "delta-t"]

    @property
    def lambda_0(self) -> float:
        return self._param("lambda_0", self._default_lambda_0)

    @property
    def fit_name(self) -> str:
        return self._param("fit_name", self._default_fit_name)

    @property
    def subtract_continuum(self) -> bool:
        return self._param("subtract_continuum", self._default_subtract_continuum)

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

        if self.y_lim is not None:
            ax.set(ylim=self.y_lim)
        ax.set_yticks(self.y_ticks, minor=False)
        ax.set_yticklabels(self.y_tick_labels, minor=False)
        return

    def _draw_spectra(self, ax: Axes, spectra: Dict[str, Spectrum1DEx], line_fits: Dict[str, List[Model]]):
        # TODO: We need a general approach to setting the color based on delta_t for these plots
        if self.lambda_0 < 5000:
            ax.set_prop_cycle(cycler(color=["b", "tab:blue", "dodgerblue", "lightskyblue"]))
        else:
            ax.set_prop_cycle(cycler(color=["tab:red", "r", "orangered", "tomato"]))

        ix = 0
        for spec_key in reversed(list(spectra.keys())):
            spectrum = spectra[spec_key]
            delta_t = self._get_spectrum_delta_t(spectrum)
            line_fit = self.__class__._get_line_fit(spec_key, self.fit_name, line_fits) if self.subtract_continuum else None
            self._draw_flux(ax, spectrum.flux, spectrum.spectral_axis, line_fit, ix, delta_t)
            ix += 1
        return

    def _draw_fits(self, ax: Axes, spectra: Dict[str, Spectrum1DEx], line_fits: Dict[str, List[Model]]):
        # TODO: We need a general approach to setting the color based on delta_t for these plots
        if self.lambda_0 < 5000:
            ax.set_prop_cycle(cycler(color=["b", "tab:blue", "dodgerblue", "lightskyblue"]))
        else:
            ax.set_prop_cycle(cycler(color=["tab:red", "r", "orangered", "tomato"]))

        ix = 0
        for fit_key in reversed(list(line_fits.keys())):
            line_fit = self.__class__._get_line_fit(fit_key, self.fit_name, line_fits)
            spectrum = spectra[fit_key]
            delta_t = self._get_spectrum_delta_t(spectrum)
            self._draw_flux(ax, line_fit(spectrum.spectral_axis), spectrum.spectral_axis, line_fit, ix, delta_t)
            ix += 1
        return

    def _draw_flux(self, ax: Axes, flux: Quantity, wavelength: Quantity, line_fit: CompoundModel, ix: int, delta_t: float):
        if self.subtract_continuum:
            # Will error if no model, or it's not one containing a continuum fit
            continuum_fit = line_fit["continuum"]
            flux = np.subtract(flux, continuum_fit(wavelength))

        if self.y_shift != 0:
            shift = (delta_t if self.y_shift_by_delta_t else ix) * self.y_shift
            flux = np.add(flux, shift * flux.unit)

            note_x_pos = self.__class__._get_annotation_x_pos(ax, 0.02)
            note_y_pos = shift + abs(self.y_shift / 5)
            ax.annotate(f"$\\Delta t$={delta_t:.2f} d",
                        xycoords="data", xy=(note_x_pos, note_y_pos), fontsize="xx-small")

        ax.plot(wavelength, flux, linestyle="-", linewidth=0.25)
        return

    def _calculate_shift_factor(self, ix: int, spectrum: Spectrum1DEx) -> float:
        shift_factor = 0
        if self.y_shift != 0:
            if self.y_shift_by_delta_t:
                mjd = spectrum.mjd
                delta_t = tm.delta_t_from_jd(tm.jd_from_mjd(mjd), self.eruption_jd)
                shift_factor = self.y_shift * delta_t
            else:
                shift_factor = self.y_shift * ix
        return shift_factor

    def _get_spectrum_delta_t(self, spectrum: Spectrum1DEx) -> float:
        mjd = spectrum.mjd
        return tm.delta_t_from_jd(tm.jd_from_mjd(mjd), self.eruption_jd)

    @classmethod
    def _get_annotation_x_pos(cls, ax: Axes, relative_position: float = 0.02) -> float:
        x_lim = ax.get_xlim()
        min_value = min(x_lim)
        max_value = max(x_lim)
        return min_value + ((max_value - min_value) * relative_position)
