from uncertainties import unumpy, ufloat_fromstr, UFloat
from plot.BasePlot import *
from plot.PlotSet import *
from utility import math_uncertainties as unc


class ColorMagnitudePlot(BasePlot):
    """
    This is a color-magnitude plot.  It is based on BasePlot as it isn't plotting against time
    and doesn't need log support on either axis.
    TODO: WIP as there is still hard coded implementation in here.
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_x_label = "$(B-V)_{int}$"
        self._default_x_lim = (-1, 1)
        self._default_x_ticks = [-1.0, -0.5, 0, 0.5, 1]

        self._default_y_label = "$M_V$"
        self._default_y_lim = (-10, 0)
        self._default_y_ticks = [-10, -8, -6, -4, -2, 0]

        # Compulsory - want a failure if these are not set
        self._default_mu = self._default_color_excess = None
        self._default_max_delta_t = 70
        return

    @property
    def mu(self):
        return self._param("mu", self._default_mu)

    @property
    def color_excess(self):
        return self._param("E(B-V)", self._default_color_excess)

    @property
    def max_delta_t(self):
        return self._param("max_delta_t", self._default_max_delta_t)

    def _configure_ax(self, ax: Axes, **kwargs):
        """
        Overriding the configuration of the target ax so we can invert the y-axis and set a limit on it
        """
        # Invert the y-axis for magnitudes - need to do this early.  Also put a limit on it.
        ax.set(ylim=self._param("y_lim", self._default_y_lim))
        ax.invert_yaxis()

        super()._configure_ax(ax, **kwargs)
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Hook into the BasePlot plot processing to enable this type to draw to the plot Axes
        """
        plot_data = kwargs["plot_data"]
        plot_sets = plot_data.plot_sets

        # we are interested in the B and V band data (TODO: remove hard coding later)
        b_set = plot_sets["2019-AAVSO/nominal/B"]
        v_set = plot_sets["2019-AAVSO/nominal/V"]
        delta_ts = np.append(np.arange(0.1, 2.0, 0.1), np.arange(2.0, self.max_delta_t, 0.5))

        for color_excess in [self.color_excess.nominal_value]:
            for mu in [self.mu.nominal_value]:
                x_data, y_data = self.__class__._calculate_color_magnitude_values(
                    b_set.fits, v_set.fits, delta_ts, color_excess, mu)

                color = "b"
                label = f"E(B-V)={color_excess:.2f}, $\\mu$={mu:.2f}"
                ax.errorbar(unumpy.nominal_values(x_data), unumpy.nominal_values(y_data),
                            # xerr=unumpy.std_devs(x_data), yerr=unumpy.std_devs(y_data),
                            label=label, fmt="D", color=color, fillstyle='full', markersize=self._marker_size * 2,
                            capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)
        return

    @classmethod
    def _calculate_color_magnitude_values(cls, b_set: FitSet, v_set: FitSet,
                                          delta_ts: [float], color_excess: UFloat, mu: UFloat):
        """
        Calculate the (intrinsic)color v (absolute)magnitude data based on the passed
        fitted lightcurves (for apparent mags), time points, colour excess and distance modulus values.
        """
        # Loop through time, sampling the apparent mag of the fit for each set
        # From this we calculate the absolute mag (from V band) and the observed color (B-V)
        abs_mag = []
        intrinsic_color = []

        for delta_t in delta_ts:
            # These will be ufloats
            B = b_set.find_y_value(delta_t)
            V = v_set.find_y_value(delta_t)
            if B is not None and V is not None:
                observed_color = B - V
                intrinsic_color.append(observed_color - color_excess)
                abs_mag.append(V - mu)
        return intrinsic_color, abs_mag
