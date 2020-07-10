from typing import Dict
from plot import SingleMagnitudeTimePlot
import numpy as np


class SingleMagnitudeAndRateTimePlot(SingleMagnitudeTimePlot):
    """
    Produces a Magnitude vs Delta-time plot for 1 or more bands on a single axis. The y-axis is inverted.
    Adds a second y-axis and plots rates vs Delta-time

    Optionally the magnitude data may be overlaid with fitted slopes.  Unlike y1, the y2 axis supports log scaling.

    The following plot params are supported (in addition to those standard for a Magnitude/Time plot);
        y2_label, y2_lim, y2_scale_log, y2_lim_log, y2_ticks_log
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2

        # Put this on the left as we'll have a second legend on the right, for the y2 axis
        self._default_legend_loc = "upper left"

        # Default settings for the second, y-axis (which can support a log scale, unlike the main (magnitude) y-axis)
        self._default_y2_label = "Count Rate (0.1 - 10 keV) [s$\\^{-1}$]"
        self._default_y2_legend_loc = "upper right"
        self._default_y2_lim = [0, 25]

        self._default_y2_scale_log = False
        self._default_y2_lim_log = [0.01, 25]
        self._default_y2_ticks_log = [1, 10, 100]

        self._y2_data_column = "rate"
        self._y2_err_column = "rate_err"
        return

    def _configure_ax(self, ax):
        # This looks after the shared x-axis and the primary y-axis
        super()._configure_ax(ax)

        # Now we set up the secondary y-axis
        self._ax2 = ax.twinx()
        self._ax2.set_ylabel(self._param("y2_label", self._default_y2_label))

        y2_scale_log = self._param("y2_scale_log", self._default_y2_scale_log)
        if y2_scale_log:
            self._ax2.set_yscale("log")
            self._ax2.set_yticks(self._param("y2_ticks_log", self._default_y2_ticks_log), minor=False)
            self._ax2.set_yticklabels(self._param("y2_ticks_log", self._default_y2_ticks_log), minor=False)
            self._ax2.set(ylim=self._param("y2_lim", self._default_y2_lim_log))
        else:
            self._ax2.set(ylim=self._param("y2_lim", self._default_y2_lim))
        return

    def _render_plot_set(self, ax, ix: int, plot_set: Dict):
        df = plot_set["df"]

        if "mag" in df.columns and "mag_err" in df.columns:
            # Magnitude data - plotted against the default y-axis
            super()._render_plot_set(ax, ix, plot_set)
        elif "rate" in df.columns and "rate_err" in df.columns:
            # Rate/count data - plotted against the secondary y-axis
            # TODO: if self._param("show_data"):
            label = self._define_data_label(plot_set, is_rate=True)
            color = plot_set["params"]['color']
            self._plot_df_to_error_bars_on_ax(self._ax2,
                                              df, self._x_data_column, self._y2_data_column, self._y2_err_column,
                                              color, label)

            # TODO: Fits
        return

    def _render_plot_sets(self, ax, plot_sets):
        super()._render_plot_sets(ax, plot_sets)

        # Once all the plots have been made we can configure the additional legend for the y2 axis
        if self._show_legend:
            self._ax2.legend(loc=self._param("y2_legend_loc", self._default_y2_legend_loc))
        return

    def _define_data_label(self, plot_set: Dict, y_shift: float = 0, is_rate=False):
        if is_rate:
            label = plot_set["params"]["label"] + (F" (shifted {y_shift:+.1f} [rate])" if y_shift != 0 else "")
        else:
            label = super()._define_data_label(plot_set, y_shift)
        return label

    def _log_scale_x_points(self, x_points):
        """
        TODO: Temp fix for the fact that currently the straight line log fit code publishes x_points as logs
        """
        return np.power(10, x_points) if self._param("x_scale_log", self._default_x_scale_log) else x_points
