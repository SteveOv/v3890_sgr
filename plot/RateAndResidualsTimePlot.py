from matplotlib.gridspec import GridSpec
from plot.RateTimePlot import *


class RateAndResidualsTimePlot(RateTimePlot):
    """
    Plot showing rate data with fits and optional second ax below with the residuals of the fit.

    In addition to the plot_params from RateTimePlot the following are supported:
        * show_residuals (True)
        * y_label_residuals (Residuals) - the y-label for the residuals sub plot (x axis is shared)
        * y_lim_residuals (-2, 2)
        * y_ticks_residuals [-2, 0, 2]
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2

        # Override the parent - as this plot is for fits/residuals it's "always" going to use a log x scale
        self._default_x_scale_log = True

        self._default_show_residuals = True
        self._default_y_label_residuals = "Residuals"
        self._default_y_lim_residuals = (-2, 2)
        self._default_y_ticks_residuals = [-2, 0, 2]
        return

    @property
    def show_residuals(self) -> bool:
        return self._param("show_residuals", self._default_show_residuals)

    @property
    def y_label_residuals(self) -> str:
        return self._param("y_label_residuals", self._default_y_label_residuals)

    @property
    def y_lim_residuals(self) -> List[float]:
        return self._param("y_lim_residuals", self._default_y_lim_residuals)

    @property
    def y_ticks_residuals(self) -> List[float]:
        return self._param("y_ticks_residuals", self._default_y_ticks_residuals)

    @property
    def y_tick_labels_residuals(self) -> str:
        return self._param("y_tick_labels_residuals", self.y_ticks_residuals)

    def _create_ax(self, fig: Figure) -> Axes:
        """
        Create the main ax, for the rate/time light curve and then the optional 2nd ax below for the residuals.
        """
        gs = GridSpec(nrows=2, ncols=1, height_ratios=[8, 2], figure=fig)

        if self.show_residuals:
            self._ax_main = fig.add_subplot(gs[0, 0])
            self._ax_res = fig.add_subplot(gs[1, 0], sharex=self._ax_main)
        else:
            self._ax_main = fig.add_subplot(gs[:, 0])
            self._ax_res = None

        # Return the main ax so that super()'s Mag/time plotting can be carried out against it
        return self._ax_main

    def _configure_ax(self, ax: Axes, **kwargs):
        # Default handling of the main ax ...
        super()._configure_ax(ax, **kwargs)

        # but super() won't know about the 2nd, residuals axis so we set it up here
        if self.show_residuals and self._ax_res is not None:
            # Don't do anything with the x-axis - it's shared with the main ax so has already been set up
            self._ax_res.set(ylim=self.y_lim_residuals, ylabel=self.y_label_residuals,
                             yticks=self.y_ticks_residuals, yticklabels=self.y_tick_labels_residuals)
            self._ax_res.grid(which='major', linestyle='-', linewidth=self.line_width * 0.75, alpha=self.alpha * 0.75)
            if self._param("x_scale_log", self._default_x_scale_log):
                self._ax_res.grid(which="minor", linestyle="-", linewidth=self.line_width * 0.5, alpha=self.alpha * 0.5)
        return

    def _draw_lightcurve_and_fit_set(self, ax: Axes, ix: int, lightcurve: Lightcurve = None, fit_set: FitSet = None):
        # Super() looks after the main ax with the rate(& fit)/time plot
        super()._draw_lightcurve_and_fit_set(ax, ix, lightcurve, fit_set)

        # now we calculate and plot the residuals to the additional ax
        if self.show_residuals and fit_set is not None and lightcurve is not None and self._ax_res is not None:
            color = lightcurve.metadata.get_or_default("color", fit_set.metadata.get_or_default("color", "k"))

            x_res, y_res = fit_set.calculate_residuals(lightcurve.x, lightcurve.y)
            self._ax_res.plot(x_res, y_res, ".", color=color, markersize=self.marker_size * 2, alpha=1, zorder=2)
        return
