from typing import Dict
from plot import SinglePlot


class ColorMagnitudePlot(SinglePlot):
    """
    TODO
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 1
        self._default_y_size = 1
        self._default_show_legend = False

        self._default_x_label = "$(B-V)_O$"
        self._default_x_lim = (-1, 1)
        self._default_x_ticks = [-1, -0.5, 0, 0.5, 1]

        self._default_y_label = "$M_V$"
        self._default_y_lim = (-10, 0)
        self._default_y_ticks = [-10, -8, -6, -4, -2, 0]

        self._E_B_V = 0.31
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

    def _render_plot_sets(self, ax, plot_sets: Dict):
        """
        Completely subclass the data rendering logic of the superclass()
        In this case we're not directly plotting photometric data,
        instead we'll do SED analysis and then plot the resulting data.
        """

        return