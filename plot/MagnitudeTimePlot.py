from plot.TimePlotSupportingLogAxes import *


class MagnitudeTimePlot(TimePlotSupportingLogAxes):
    """
    Produces a Magnitude vs Delta-time plot for 1 or more bands on a single axis.
    The y-axis is inverted to match the needs of a magnitude scale.  Y-axis not "log-able" - mags already logs.

    The following plot params are supported (in addition to those of parent; SinglePlotSupportingLogAxes);
        * y_lim (5.8, 19) - set the limits of the y-axis
    """

    def __init__(self, plot_params: Dict):
        # y-axis - not "log-able" and mags are already a log scale
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=False)

        self._default_x_label = "$\\Delta t$ [days]"
        self._default_y_label = f"Apparent magnitude [mag]"
        self._default_y_lim = (5, 19)
        return

    @property
    def y_lim(self) -> List[float]:
        return self._param("y_lim", self._default_y_lim)

    def _configure_ax(self, ax: Axes, **kwargs):
        """
        Overriding the configuration of the target ax so we can invert the y-axis and set a limit on it
        """
        # Invert the y-axis for magnitudes - need to do this early.  Also put a limit on it (which super() does not).
        ax.set(ylim=self.y_lim)
        ax.invert_yaxis()
        super()._configure_ax(ax, **kwargs)
        return

    def _define_data_label(self, label: str, y_shift: float = 0):
        return label + (F" (shifted {y_shift:+.1f} mag)" if y_shift != 0 else "")

