from typing import Dict
from plot.SinglePlotSupportingLogAxes import SinglePlotSupportingLogAxes
from plot.PlotSet import PlotSet


class SingleRateTimePlot(SinglePlotSupportingLogAxes):
    """
    Produces a Rate vs Delta-time plot for 1 or more bands on a single axis.  Both axes support log scaling.
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=True)

        self._default_show_data = True
        self._default_show_fits = False

        # x-axis - expected to cover a range of 0 to 100 days (linear and log)
        self._default_x_label = "$\\Delta t$ [days]"
        self._default_x_lim = (-1, 100)
        self._default_x_lim_log = (0.014, 100)

        # y-axis is "log-able" for these rate plots
        self._default_y_label = "Count Rate [ph s$^{-1}$]"
        self._default_y_lim_log = [0.01, 31]
        self._default_t_ticks_log = [0.1, 1, 10]
        return

    def _configure_ax(self, ax):
        super()._configure_ax(ax)

        # Super supports setting the y-axis to log, but doesn't set a limit or ticks  as it doesn't know
        # what sort of data will be shown.  Here we know we are showing rates so we can default to reasonable values.
        y_scale_log = self._y_axis_supports_log & self._param("y_scale_log", self._default_y_scale_log)
        if y_scale_log:
            ax.set(ylim=self._param("y_lim", self._default_y_lim_log))
            ax.set_yticks(self._param("y_ticks", self._default_t_ticks_log), minor=False)
            ax.set_yticklabels(self._param("y_ticks", self._default_t_ticks_log), minor=False)
        return

    def _render_plot_set(self, ax, ix: int, ps: PlotSet):
        show_data = self._param("show_data", self._default_show_data)
        show_fits = self._param("show_fits", self._default_show_fits)
        y_shift = self._param("y_shift", 0) * ix
        label = self._define_data_label(ps.label, y_shift)

        if show_data:
            # super class plots the data as a set of error bars
            super()._render_plot_set(ax, ix, ps)

        if show_fits and ps.fits is not None:
            color = ps.color
            for fit in ps.fits:
                fit_line, = self._plot_points_to_lines_on_ax(
                    ax, fit.linear_x_endpoints, fit.y_endpoints, color, y_shift=y_shift)
                if not show_data and len(label) > 0:
                    fit_line.set_label(label)
                    label = ""  # Stop the label being repeated for each subsequent fit in this plot_set's fits
        return

