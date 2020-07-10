from abc import ABC
from typing import Dict, List
from plot import SinglePlot


class SinglePlotSupportingLogAxes(SinglePlot, ABC):
    """
    Extends SinglePlot adding support for explicitly using log axes
    """

    def __init__(self, plot_params: Dict, x_axis_supports_log: bool = False, y_axis_supports_log: bool = False):

        super().__init__(plot_params)

        # It is expected that these values may be overridden by subclasses
        self._x_axis_supports_log = x_axis_supports_log
        self._y_axis_supports_log = y_axis_supports_log

        self._default_x_scale_log = False
        self._default_x_lim_log = (0.1, 100)
        self._default_x_ticks_log = [0.1, 1, 10, 100]

        self._default_y_scale_log = False
        # Don't impose a default limit on the y-scale, as it needs to be responsive to the data.
        return

    def _configure_ax(self, ax):
        """
        Configure the ax, supporting the use of log scale on either the x or y (or both) axis
        """
        # Get the super class to do the basic config.  We'll override if any log axes specified.
        super()._configure_ax(ax)

        x_scale_log = self._x_axis_supports_log & self._param("x_scale_log", self._default_x_scale_log)
        y_scale_log = self._y_axis_supports_log & self._param("y_scale_log", self._default_y_scale_log)

        if x_scale_log:
            ax.set_xscale("log")
            ax.set_xticks(self._param("x_ticks", self._default_x_ticks_log), minor=False)
            ax.set_xticklabels(self._param("x_ticks", self._default_x_ticks_log), minor=False)
            ax.set(xlim=self._param("x_lim", self._default_x_lim_log))

        if y_scale_log:
            ax.set_yscale("log")

        if x_scale_log | y_scale_log:
            ax.grid(which="minor", linestyle="-", linewidth=self._line_width, alpha=0.1)
        return
