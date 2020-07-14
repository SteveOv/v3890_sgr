from typing import Dict
from matplotlib.gridspec import GridSpec
from plot import MagnitudeTimePlot, PlotSet


class MagnitudeAndResidualsTimePlot(MagnitudeTimePlot):
    """
    Plot showing magnitude data with fits and optional second ax below with the residuals of the fit.

    In addition to the plot_params from MagnitudeTimePlot the following are supported:
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
        self._default_y_label_residuals = "Residuals [mag]"
        self._default_y_lim_residuals = (-2, 2)
        self._default_y_ticks_residuals = [-2, 0, 2]
        return

    @property
    def show_residuals(self):
        return self._param("show_residuals", self._default_show_residuals)

    @property
    def y_label_residuals(self):
        return self._param("y_label_residuals", self._default_y_label_residuals)

    @property
    def y_lim_residuals(self):
        return self._param("y_lim_residuals", self._default_y_lim_residuals)

    @property
    def y_ticks_residuals(self):
        return self._param("y_ticks_residuals", self._default_y_ticks_residuals)

    def _create_ax(self, fig):
        """
        Create the main ax, for the magnitude/time light curve and then the optional 2nd ax below for the residuals.
        Fully replace the super's implementation here as we need to use a GridSpec to manage the layout
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

    def _configure_ax(self, ax):
        # Default handling of the main ax ...
        super()._configure_ax(ax)

        # but super() won't know about the 2nd axis so we set it up here
        if self.show_residuals and self._ax_res is not None:
            # Don't do anything with the x-axis - it's shared with the main ax so has already been set up
            self._ax_res.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
            self._ax_res.set(ylim=self.y_lim_residuals)
            self._ax_res.set_ylabel(self.y_label_residuals)
            self._ax_res.set_yticks(self.y_ticks_residuals)
            self._ax_res.invert_yaxis()
            if self._param("x_scale_log", self._default_x_scale_log):
                self._ax_res.grid(which="minor", linestyle="-", linewidth=self._line_width, alpha=0.1)
        return

    def _draw_plot_set(self, ax, ix: int, ps: PlotSet):
        # Super() looks after the main ax with the magnitude/time plot
        super()._draw_plot_set(ax, ix, ps)

        # now we plot the residuals to the additional ax
        if self.show_residuals and self._ax_res is not None:
            # TODO: will need revisiting if the Log Fits are reworked to not take df and to work in logs internally
            x_points, y_points = ps.fits.calculate_residuals(
                ps.df, "day", "rate" if ps.data_type == "rate" else "mag")
            self._ax_res.plot(
                x_points, y_points, ".", color=ps.color, markersize=self._marker_size * 2, alpha=1, zorder=2)
        return
