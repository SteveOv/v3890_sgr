from plot.TimePlotSupportingLogAxes import *


class RateTimePlot(TimePlotSupportingLogAxes):
    """
    Produces a Rate vs Delta-time plot for 1 or more bands on a single axis.  Both axes support log scaling.

    The following plot params are supported (in addition to those of parent; SinglePlotSupportingLogAxes);
        * y_lim (y_scale_log == True) [0.01, 31] - set the limits of the log y-axis
        * y_ticks (y_scale_log == True) [0.1, 1, 10] - the ticks and tick labels of the log y-axis
    """

    def __init__(self, plot_params: Dict, x_axis_supports_log: bool = True, y_axis_supports_log: bool = True):
        super().__init__(plot_params, x_axis_supports_log, y_axis_supports_log)

        # x-axis - expected to cover a range of 0 to 100 days (linear and log)
        self._default_x_label = "$\\Delta t$ [days]"

        # y-axis is "log-able" for these rate plots.  We also have y_lim as we know what is reasonable for these data.
        self._default_y_label = "Count Rate [ph s$^{-1}$]"
        self._default_y_lim = [-2, 31]
        self._default_y_ticks = [0, 10, 20, 30]
        self._default_y_lim_log = [0.01, 31]
        self._default_y_ticks_log = [0.1, 1, 10]
        return

    @property
    def y_lim(self) -> List[float]:
        return self._param("y_lim", self._default_y_lim_log if self.y_scale_log else self._default_y_lim)

    @property
    def y_ticks(self) -> List[float]:
        return self._param("y_ticks", self._default_y_ticks_log if self.y_scale_log else self._default_y_ticks)

    def _configure_ax(self, ax: Axes):
        super()._configure_ax(ax)

        # Super supports setting the y-axis to log, but doesn't set a limit or ticks  as it doesn't know
        # what sort of data will be shown.  Here we know we are showing rates so we can default to reasonable values.
        if self.y_scale_log:
            ax.set(ylim=self.y_lim, yticks=self.y_ticks, yticklabels=self.y_ticks)
        return

