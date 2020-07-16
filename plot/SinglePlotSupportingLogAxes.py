from plot.SinglePlot import *


class SinglePlotSupportingLogAxes(SinglePlot, ABC):
    """
    Extends SinglePlot adding support for plot_params to configure the use of log x and/or y axes.
    Subclasses can set the x/y_axis_supports_log param on __init__() to control whether an axis may be so configured.

    Adds support for the config settings;
        * x_scale_log / y_scale_log (False) - whether to use a log scale on said axis
    """

    def __init__(self, plot_params: Dict, x_axis_supports_log: bool = False, y_axis_supports_log: bool = False):
        super().__init__(plot_params)

        # Mechanism by which subclasses can restrict/allow which axis is allowed to be set to a log scale
        self._x_axis_supports_log = x_axis_supports_log
        self._y_axis_supports_log = y_axis_supports_log

        # Default log scale for the x-axis is 0-100 days
        self._default_x_scale_log = False
        self._default_x_lim_log = (0.01, 100)
        self._default_x_ticks_log = [0.1, 1, 10, 100]

        self._default_y_scale_log = False
        # Don't impose a default limit on the y-scale, as it needs to be responsive to the data.
        return

    @property
    def x_scale_log(self) -> bool:
        return self._x_axis_supports_log & self._param("x_scale_log", self._default_x_scale_log)

    @property
    def x_lim(self) -> List[float]:
        return self._param("x_lim", self._default_x_lim_log) if self.x_scale_log else super().x_lim

    @property
    def x_ticks(self) -> List[float]:
        return self._param("x_ticks", self._default_x_ticks_log) if self.x_scale_log else super().x_ticks

    @property
    def y_scale_log(self) -> bool:
        return self._y_axis_supports_log & self._param("y_scale_log", self._default_y_scale_log)

    def _configure_ax(self, ax: Axes):
        """
        Configure the ax, supporting the use of log scale on either the x or y (or both) axis
        """
        # Get the super class to do the basic config.  We'll override if any log axes specified.
        super()._configure_ax(ax)

        if self.x_scale_log:
            ax.set_xscale("log")
            ax.set(xlim=self.x_lim, xticks=self.x_ticks, xticklabels=self.x_ticks)

        if self.y_scale_log:
            ax.set_yscale("log")

        if self.x_scale_log | self.y_scale_log:
            ax.grid(which="minor", linestyle="-", linewidth=self._line_width, alpha=0.2)
        return
