from plot.BasePlot import *
from fitting.FitSet import *


class TimePlot(BasePlot, ABC):
    """
    Produces a data vs time plot for 1+ sets of data on a single axis, optionally overlaying with fitted lines.
    The following plot params are supported (in addition to the standard params defined by BasePlot);
        * show_data (True) - plot the raw data
        * show_fits (False) - draw the line fits
        * show_epochs / show_epoch_labels (False/False) - controls drawing of epoch lines & labels on x-axis
        * y_shift (0) - optional shift in the y-axis for each subsequent data_set
    For each PlotSet the following rate_params are supported:
        * color
        * label
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_show_data = True
        self._default_show_fits = False
        self._default_show_epochs = False
        self._default_show_epoch_labels = False

        self._default_y_shift = 0
        return

    @property
    def show_data(self) -> bool:
        return self._param("show_data", self._default_show_data)

    @property
    def show_fits(self) -> bool:
        return self._param("show_fits", self._default_show_fits)

    @property
    def show_epochs(self) -> bool:
        return self._param("show_epochs", self._default_show_epochs)

    @property
    def show_epoch_labels(self) -> bool:
        return self._param("show_epoch_labels", self._default_show_epoch_labels)

    @property
    def y_shift(self) -> float:
        return self._param("y_shift", self._default_y_shift)

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override of the BasePlot abstract method where we actually get to draw data onto the Axes.
        """
        # Potential hooks for the subtype to plot each lightcurve & fit_set
        lightcurves = kwargs["lightcurves"] if "lightcurves" in kwargs else None
        fit_sets = kwargs["fit_sets"] if "fit_sets" in kwargs else None
        self._draw_lightcurves_and_fit_sets(ax, lightcurves, fit_sets)

        # Potential hook for subtype to choose whether/how to render epoch data
        epochs = kwargs["epochs"] if "epochs" in kwargs else None
        if self.show_epochs:
            self._draw_epochs(ax, epochs)
        return

    def _draw_lightcurves_and_fit_sets(self, ax: Axes, lightcurves: Dict, fit_sets: Dict):
        # Match up the lightcurves and fit sets.
        ix = 0
        for lightcurve, fit_set in self.__class__._pair_lightcurves_and_fit_sets(lightcurves, fit_sets):
            self._draw_lightcurve_and_fit_set(ax, ix, lightcurve, fit_set)
            ix += 1
        return

    def _draw_lightcurve_and_fit_set(self, ax: Axes, ix: int, lightcurve: Lightcurve = None, fit_set: FitSet = None):
        this_y_shift = self.y_shift * ix

        # We only want to show one color & label, so prioritise the lightcurve label but fall back on the fit set.
        label = ""
        color = "k"
        if lightcurve is not None:
            label = self._define_data_label(lightcurve.label, this_y_shift)
            default_color = fit_set.metadata.get_or_default("color", "k") if fit_set is not None else "k"
            color = lightcurve.metadata.get_or_default("color", default_color)
        elif fit_set is not None:
            label = self._define_data_label(fit_set.label, this_y_shift)
            default_color = lightcurve.metadata.get_or_default("color", "k") if lightcurve is not None else "k"
            color = fit_set.metadata.get_or_default("color", default_color)

        # Optionally render the lightcurve data
        if self.show_data and lightcurve is not None:
            data_alpha = self.alpha / 3 if self.show_fits else self.alpha
            self._plot_points_to_error_bars_on_ax(ax, x_points=lightcurve.x, y_points=lightcurve.y,
                                                  y_err_points=lightcurve.y_err, line_width=self.line_width / 2,
                                                  color=color, alpha=data_alpha, label=label, y_shift=this_y_shift)
            label = None  # Make sure the label isn't used again

        # Optionally draw the associated fitted lines
        if self.show_fits and fit_set is not None:
            fit_set.draw_on_ax(ax, color, label=label,
                               line_width=self.line_width, alpha=self.alpha * 2, z_order=2.0, y_shift=this_y_shift)
        return

    def _draw_epochs(self, ax: Axes, epochs: Dict[str, float]):
        if epochs is not None and len(epochs) > 0:
            x_pos = list(epochs.values())
            text = list(epochs.keys()) if self.show_epoch_labels else None
            self._draw_vertical_lines(ax, x=x_pos, text=text, color="gray", line_style="--")
        return

    def _define_data_label(self, label: str, shift_by: float = 0) -> str:
        return label + (F" (shifted {shift_by:+.1f})" if shift_by != 0 else "")

    @classmethod
    def _pair_lightcurves_and_fit_sets(cls, lightcurves: Dict, fit_sets: Dict) -> List[Tuple[Lightcurve, FitSet]]:
        """
        Produce a master list of lightcurves and fitsets paired where possible.
        Each entry is a tuple of a lightcurve and fitset (either may be null if no match found).
        The ordering is prioritised by the lightcurves, then fit sets.
        """
        pairs = list()

        # Try to match up lightcurve and fit_set for plotting.  The default method is
        # through fit_set metadata item on the lightcurves.  Do we have any?
        explicit_fits = []
        if lightcurves is not None:
            explicit_fits = {k: v for k, v in lightcurves.items() if "fit_set" in v.metadata}

        if len(explicit_fits) > 0 or lightcurves is None or fit_sets is None or len(lightcurves) != len(fit_sets):
            # At least one explicitly specified fit_set or the number of lightcurve/fit_sets don't match up.
            # We will go through the lightcurves matching where instructed ...
            fs_keys_used = []
            if lightcurves is not None:
                for lc_key, lightcurve in lightcurves.items():
                    fs_key = lightcurve.metadata.get_or_default("fit_set", None)
                    if fs_key is not None:
                        fit_set = fit_sets[fs_key] if fs_key in fit_sets else None
                        fs_keys_used.append(fs_key)
                    else:
                        fit_set = None
                    pairs.append((lightcurve, fit_set))

            # ... then pick up any fit_sets not matched to a lightcurve
            if fit_sets is not None:
                orphans = {k: v for k, v in fit_sets.items() if k not in fs_keys_used}
                for fs_key, fit_set in orphans.items():
                    pairs.append((None, fit_set))

        else:
            # No explicit fit_set links, but the number of lightcurves & fit_sets match so fall back on pairing in step
            for lightcurve, fit_set in zip(lightcurves.values(), fit_sets.values()):
                pairs.append((lightcurve, fit_set))
        return pairs
