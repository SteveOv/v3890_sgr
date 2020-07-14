from typing import Dict
from matplotlib.gridspec import GridSpec
from plot.RateTimePlot import RateTimePlot
from plot.PlotSet import PlotSet


class RatesAndRatioTimePlot(RateTimePlot):
    """
    Produces a 3 x Rate vs log(Delta-time) plots. Specifically for plotting hard / soft / ratio XRT/X-ray plots.

    Adds the following plot_params to (RateTimePlot):
        * y_label_hard_data, y_label_soft_data, y_label_ratio
        * y_lim_ratio, y_ticks_ratio (existing y_lim and y_ticks params apply to hard/soft data)
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # override the "default" default sizing
        self._default_x_size = 2
        self._default_y_size = 2

        self._default_y_label_hard_data = "Hard: 1.5 - 10 keV [s$^{-1}$]"
        self._default_y_label_soft_data = "Soft: 0.3 - 1.5 keV [s$^{-1}$]"
        self._default_y_label_ratio = "Ratio"
        self._default_y_lim_ratio = (-2, 21)
        self._default_y_ticks_ratio = [0, 10, 20]
        self._default_y_lim_ratio_log = (0.01, 21)
        self._default_y_ticks_ratio_log = [0.1, 1, 10]
        return

    @property
    def y_label_hard_data(self):
        return self._param(f"y_label_hard_data", self._default_y_label_hard_data)

    @property
    def y_label_soft_data(self):
        return self._param(f"y_label_soft_data", self._default_y_label_soft_data)

    @property
    def y_label_ratio(self):
        return self._param("y_label_ratio", self._default_y_label_ratio)

    @property
    def y_lim_ratio(self):
        return self._param("y_lim_ratio",
                           self._default_y_lim_ratio_log if self.y_scale_log else self._default_y_lim_ratio)

    @property
    def y_ticks_ratio(self):
        return self._param("y_ticks_ratio",
                           self._default_y_ticks_ratio_log if self.y_scale_log else self._default_y_ticks_ratio)

    @property
    def y_shift(self):
        # Never allow a y-shift to be applied.
        return 0

    def _create_ax(self, fig):
        gs = GridSpec(nrows=3, ncols=1, height_ratios=[3, 3, 2], figure=fig)
        self._ax_ratio = fig.add_subplot(gs[2, 0])
        self._ax_hard = fig.add_subplot(gs[0, 0], sharex=self._ax_ratio)
        self._ax_soft = fig.add_subplot(gs[1, 0], sharex=self._ax_ratio)

        # Only this ax will have the title/legend added as appropriate by the super classes.
        return self._ax_hard

    def _configure_ax(self, ax):
        self._ax_hard.set_ylabel(self.y_label_hard_data)
        self._ax_soft.set_ylabel(self.y_label_soft_data)
        for ax in [self._ax_ratio, self._ax_hard, self._ax_soft]:
            if ax is self._ax_ratio:
                # Configure the ratio ax ...
                if self.y_scale_log:
                    ax.set_yscale("log")
                ax.set_ylabel(self.y_label_ratio)
                ax.set(xlim=self.x_lim, ylim=self.y_lim_ratio)
                ax.set_yticks(self.y_ticks_ratio, minor=False)
                ax.set_yticklabels(self.y_ticks_ratio, minor=False)

                # ... and the shared x-axis.
                if self.x_scale_log:
                    ax.set_xscale("log")
                ax.set_xlabel(self.x_label)
                ax.set_xticks(self.x_ticks, minor=False)
                ax.set_xticklabels(self.x_ticks, minor=False)
            else:
                # Configure the hard/soft ax
                if self.y_scale_log:
                    ax.set_yscale("log")
                ax.set(xlim=self.x_lim, ylim=self.y_lim)
                ax.set_yticks(self.y_ticks, minor=False)
                ax.set_yticklabels(self.y_ticks, minor=False)

            # Grids, where necessary, on all axes
            ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
            if self.y_scale_log | self.x_scale_log:
                ax.grid(which="minor", linestyle="-", linewidth=self._line_width, alpha=0.1)
        return

    def _draw_plot_set(self, ax, ix: int, ps: PlotSet):
        # Work out what we are plotting here so we know which ax to plot it on.
        # TODO: add properties to PlotSet which publish what type of data (band, hard/soft/PC/WT rate, ratio) carried.
        if "hard_data" in ps.name:
            super()._draw_plot_set(self._ax_hard, ix, ps)
        elif "soft_data" in ps.name:
            super()._draw_plot_set(self._ax_soft, ix, ps)
        elif "hardness_ratio" in ps.name:
            super()._draw_plot_set(self._ax_ratio, ix, ps)
        return
