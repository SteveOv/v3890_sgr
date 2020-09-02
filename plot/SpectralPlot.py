from plot.BasePlot import *
from spectroscopy import *


class SpectralPlot(BasePlot, ABC):
    """
    Base class for spectral plots.
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_show_legend = False
        self._default_show_data = True
        self._default_show_fits = False

        self._default_x_label = "Wavelength"
        self._default_y_label = "Arbitrary flux"

        self._default_y_lim = None
        self._default_y_ticks = []
        self._default_y_tick_labels = []
        return

    @property
    def show_data(self) -> bool:
        return self._param("show_data", self._default_show_data)

    @property
    def show_fits(self) -> bool:
        return self._param("show_fits", self._default_show_fits)

    @property
    def y_lim(self):
        return self._param("y_lim", self._default_y_lim)

    @property
    def y_ticks(self) -> List[float]:
        return self._param("y_ticks", self._default_y_ticks)

    @property
    def y_tick_labels(self) -> List[str]:
        return self._param("y_tick_labels", self._default_y_tick_labels)

    @property
    def eruption_jd(self) -> float:
        return self._param("eruption_jd", None)

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override from super(), for plotting their data to the passed Axes
        """
        spectra = kwargs["spectra"] if "spectra" in kwargs else None
        line_fits = kwargs["line_fits"] if "line_fits" in kwargs else None

        if self.show_data:
            self._draw_spectra(ax, spectra, line_fits)

        if self.show_fits:
            self._draw_fits(ax, spectra, line_fits)
        return

    @abstractmethod
    def _draw_spectra(self, ax: Axes, spectra: Dict[str, Spectrum1DEx], line_fits: Dict[str, List[Model]]):
        pass

    @abstractmethod
    def _draw_fits(self, ax: Axes, spectra: Dict[str, Spectrum1DEx], line_fits: Dict[str, List[Model]]):
        pass

    @classmethod
    def _get_line_fit(cls, fit_key: str, model_name: str, line_fits: Dict[str, List[Model]]):
        spec_line_fits = line_fits[fit_key] if (line_fits is not None and fit_key in line_fits) else None
        line_fit = next((f for f in spec_line_fits if f.name == model_name), None)
        if spec_line_fits is None:
            raise (KeyError(f"Cannot find line_fit name '{fit_key}'"))
        return line_fit

    @classmethod
    def _get_continuum_subtracted_flux(cls, spectrum: Spectrum1D, line_fit: CompoundModel) -> Quantity:
        # Throws in IndexError if not found (it should be there!).
        continuum_fit = line_fit["continuum"]
        continuum_flux = continuum_fit(spectrum.spectral_axis)
        return np.subtract(spectrum.flux, continuum_flux)
