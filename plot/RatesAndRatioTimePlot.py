from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from plot import BasePlot, PlotData, PlotSet


class RatesAndRatioTimePlot(BasePlot):
    """
    Produces a 3 x Rate vs log(Delta-time) plots. Specifically for plotting hard / soft / ratio XRT/X-ray plots.
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2

        self._default_x_lim = (0.01, 100)
        self._default_x_ticks = np.arange(0, 110, 10)
        self._default_x_ticks_log = [0.1, 1, 10, 100]

        self._default_y_lim_ratio = (-2, 21)
        self._default_y_ticks_ratio = [0, 10, 20]
        self._default_y_lim_ratio_log = (0.01, 21)

        self._default_y_lim = (-2, 31)
        self._default_y_ticks = [0, 10, 20, 30]
        self._default_y_lim_log = (0.01, 41)

        self._default_y_ticks_log = [0.1, 1, 10] # Rates and Ratios use the same log ticks/scale
        return

    def _render_plot(self, plot_data: PlotData, title: str) -> plt.figure:

        fig = plt.figure(figsize=(self._x_size, self._y_size), constrained_layout=True)
        gs = GridSpec(nrows=3, ncols=1, height_ratios=[3, 3, 2], figure=fig)

        x_lim = self._param("x_lim", (0.01, 100))
        y_scale_log = self._param("y_scale_log", False)
        x_scale_log = self._param("x_scale_log", False)

        for sub_plot_type in ["hardness_ratio", "soft_data", "hard_data"]:
            if sub_plot_type == "hardness_ratio":
                ax = fig.add_subplot(gs[2, 0])
                ax.set_ylabel(self._param("y_label_ratio", "Ratio"))

                if y_scale_log:
                    ax.set_yscale("log")
                    ax.set(xlim=x_lim, ylim=self._param("y_lim_ratio", self._default_y_lim_ratio_log))
                    ax.set_yticks(self._param("y_ticks_ratio", self._default_y_ticks_log), minor=False)
                    ax.set_yticklabels(self._param("y_ticks_ratio", self._default_y_ticks_log), minor=False)
                else:
                    ax.set(xlim=x_lim, ylim=self._param("y_lim_rate", self._default_y_lim_ratio))
                    ax.set_yticks(self._param("x_ticks_ratio", self._default_y_ticks_ratio), minor=False)

                # We are using a shared x-axis, so x-ticks/labels only on this bottom subplot.  Grids on all.
                ax.set_xlabel(self._param("x_label", "$\\Delta t$ [days]"))
                if x_scale_log:
                    ax.set_xscale("log")
                    ax.set_xticks(self._param("x_ticks", self._default_x_ticks_log), minor=False)
                    ax.set_xticklabels(self._param("x_ticks", self._default_x_ticks_log), minor=False)
                else:
                    ax.set_xticks(self._param("x_ticks", self._default_x_ticks), minor=False)
            else:
                if sub_plot_type == "hard_data":
                    ax = fig.add_subplot(gs[0, 0], sharex=ax)
                    ax.set_ylabel(self._param(f"y_label_{sub_plot_type}", "Hard: 1.5 - 10 keV [s$^{-1}$]"))
                else:
                    ax = fig.add_subplot(gs[1, 0], sharex=ax)
                    ax.set_ylabel(self._param(f"y_label_{sub_plot_type}", "Soft: 0.3 - 1.5 keV [s$^{-1}$]"))

                if y_scale_log:
                    ax.set_yscale("log")
                    ax.set(xlim=x_lim, ylim=self._param("y_lim", self._default_y_lim_log))
                    ax.set_yticks(self._param("y_ticks", self._default_y_ticks_log), minor=False)
                    ax.set_yticklabels(self._param("y_ticks", self._default_y_ticks_log), minor=False)
                else:
                    ax.set(xlim=x_lim, ylim=self._param("y_lim", self._default_y_lim))
                    ax.set_yticks(self._param("y_ticks", self._default_y_ticks), minor=False)

            ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
            if y_scale_log | x_scale_log:
                ax.grid(which="minor", linestyle="-", linewidth=self._line_width, alpha=0.1)

            # OK, now we can go through each band and derive information from it and plot its data
            # Reverse the order of the bands so the labels match the vertical displacement of the curves
            for plot_set_key in plot_data.plot_sets.keys():
                if sub_plot_type in plot_set_key:
                    ps = plot_data.plot_sets[plot_set_key]
                    color = ps.color
                    label = ps.label

                    ax.errorbar(ps.x, ps.y, yerr=ps.y_err, label=label,
                                fmt=",", color=color, fillstyle='full', markersize=self._marker_size, capsize=1,
                                ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)

            # Only show the title and legend/key once, in the top subplot.
            if sub_plot_type == "hard_data":
                ax.legend(loc=self._legend_loc)
                if self._show_title and title is not None:
                    ax.set_title(title)
        return fig
