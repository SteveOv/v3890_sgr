from plot.MagnitudeTimePlot import *


class MagnitudeAndRateTimePlot(MagnitudeTimePlot):
    """
    Produces a Magnitude vs Delta-time plot for 1 or more bands on a single axis. The y-axis is inverted.
    Adds a second y-axis and plots rates vs Delta-time

    The following plot params are supported (in addition to those standard for a Magnitude/Time plot);
        * y2_legend_loc (upper right) - location of the legend for the secondary (y2) axis
        * y2_label - label for the secondary axis
        * y2_scale_log - the secondary y-axis supports a log scale (unlike the primary)
        * y2_lim - the limits on the secondary y-axis
        * y2_ticks - and the ticks and tick labels on the secondary y-axis
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # Override the "default" defaults
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_legend_loc = "upper left"  # Put this on the left as the y2 legend is best placed on the right

        # Default settings for the second, y-axis (which can support a log scale, unlike the main (magnitude) y-axis)
        self._default_y2_legend_loc = "upper right"
        self._default_y2_label = "X-ray Count Rate [ph s$^{-1}$]"
        self._default_y2_lim = [0, 25]
        self._default_y2_ticks = [0, 10, 20, 30]

        self._default_y2_scale_log = False
        self._default_y2_lim_log = [0.01, 25]
        self._default_y2_ticks_log = [1, 10, 100]
        return

    @property
    def y2_legend_loc(self) -> str:
        return self._param("y2_legend_loc", self._default_y2_legend_loc)

    @property
    def y2_label(self) -> str:
        return self._param("y2_label", self._default_y2_label)

    @property
    def y2_lim(self) -> List[float]:
        return self._param("y2_lim", self._default_y2_lim_log if self.y2_scale_log else self._default_y2_lim)

    @property
    def y2_ticks(self) -> List[float]:
        return self._param("y2_ticks", self._default_y2_ticks_log if self.y2_scale_log else self._default_y2_ticks)

    @property
    def y2_scale_log(self) -> bool:
        return self._param("y2_scale_log", self._default_y2_scale_log)

    def _configure_ax(self, ax: Axes):
        # This looks after the shared x-axis and the primary y-axis
        super()._configure_ax(ax)

        # Now we set up the secondary y-axis
        self._ax2 = ax.twinx()

        # Rotate the label so that "down" is towards the axis.
        self._ax2.set_ylabel(self.y2_label, rotation=270)

        if self.y2_scale_log:
            self._ax2.set_yscale("log")
        self._ax2.set_yticks(self.y2_ticks, minor=False)
        self._ax2.set_yticklabels(self.y2_ticks, minor=False)
        self._ax2.set(ylim=self.y2_lim)
        return

    def _draw_plot_set(self, ax: Axes, ix: int, ps: PlotSet):
        if ps.data_type == "band":
            # Magnitude data - plotted against the default y-axis
            super()._draw_plot_set(ax, ix, ps)
        elif ps.data_type == "rate":
            # Rate/count data - make sure it's plotted against the secondary y-axis
            super()._draw_plot_set(self._ax2, ix, ps)
        return

    def _draw_plot_sets(self, ax: Axes, plot_sets: Dict[str, PlotSet]):
        super()._draw_plot_sets(ax, plot_sets)

        # Once all the plots have been made we can configure the additional legend for the y2 axis
        if self.show_legend:
            self._ax2.legend(loc=self.y2_legend_loc)
        return

    def _define_data_label(self, label: str, y_shift: float = 0, is_rate=False) -> str:
        if is_rate:
            label = label + (F" (shifted {y_shift:+.1f} [rate])" if y_shift != 0 else "")
        else:
            label = super()._define_data_label(label, y_shift)
        return label

