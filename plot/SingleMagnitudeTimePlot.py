from typing import Dict
import numpy as np
from plot import SinglePlotSupportingLogAxes


class SingleMagnitudeTimePlot(SinglePlotSupportingLogAxes):
    """
    Produces a Magnitude vs Delta-time plot for 1 or more bands on a single axis.
    The y-axis is inverted and optionally the data may be overlaid with fitted slopes.
    The following plot params are supported (in addition to the standard params);
        show_data (True) - plot the raw data
        show_fits (False) - draw the line fits
        y_lim (5.8, 19) - set the limits of the y-axis
        y_shift (0) - value to shift successive print sets in the y-direction
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=False)

        # x-axis - expected to cover a range of 0 to 100 days (linear and log)
        self._default_x_label = "$\\Delta t$ [days]"
        self._default_x_lim = (-1, 100)
        self._default_x_lim_log = (0.014, 100)

        # y-axis - not "log-able" and mags are already a log scale
        self._default_y_label = f"Apparent magnitude [mag]"
        self._default_y_lim = (5.8, 19)

        self._x_data_column = "day"
        self._y_data_column = "mag"
        self._y_err_column = "mag_err"
        return

    def _configure_ax(self, ax):
        """
        Overriding the configuration of the target ax so we can invert the y-axis and set a limit on it
        """
        # Invert the y-axis for magnitudes - need to do this early.  Also put a limit on it.
        ax.set(ylim=self._param("y_lim", self._default_y_lim))
        ax.invert_yaxis()

        super()._configure_ax(ax)
        return

    def _render_plot_set(self, ax, ix: int, plot_set: Dict):
        show_data = self._param("show_data", True)
        show_fits = self._param("show_fits", False)
        y_shift = self._param("y_shift", 0) * ix
        label = self._define_data_label(plot_set, y_shift)

        if show_data:
            # super class plots the data as a set of error bars
            super()._render_plot_set(ax, ix, plot_set)

        if show_fits:
            color = plot_set["params"]['color']
            for fit in plot_set['fits']:
                x_points = self._log_scale_x_points(fit.x_points)
                fit_line, = self._plot_points_to_lines_on_ax(ax, x_points, fit.y_points, color, y_shift=y_shift)
                if not show_data and len(label) > 0:
                    fit_line.set_label(label)
                    label = ""  # Stop the label being repeated for each subsequent fit in this plot_set's fits
        return

    def _define_data_label(self, plot_set: Dict, y_shift: float = 0):
        label = plot_set["params"]["label"]
        return label + (F" (shifted {y_shift:+.1f} mag)" if y_shift != 0 else "")

    def _log_scale_x_points(self, x_points):
        """
        TODO: Temp fix for the fact that currently the straight line log fit code publishes x_points as logs
        """
        return np.power(10, x_points) if self._param("x_scale_log", self._default_x_scale_log) else x_points
