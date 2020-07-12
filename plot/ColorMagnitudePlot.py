from typing import Dict
import numpy as np
from uncertainties import unumpy, ufloat_fromstr
from plot import SinglePlot, PlotSet


class ColorMagnitudePlot(SinglePlot):
    """
    TODO
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 1
        self._default_y_size = 1
        self._default_show_legend = True

        self._default_x_label = "$(B-V)_{int}$"
        self._default_x_lim = (-1, 1)
        self._default_x_ticks = [-1.0, -0.5, 0, 0.5, 1]

        self._default_y_label = "$M_V$"
        self._default_y_lim = (-10, 0)
        self._default_y_ticks = [-10, -8, -6, -4, -2, 0]

        self._e_bv = ufloat_fromstr(self._param("E(B-V)", None))   # Compulsory - want a failure if this isn't set
        self._mu = ufloat_fromstr(self._param("mu", None))
        self._a_v = self._param("A_V", 3.1)
        self._max_delta_t = self._param("max_delta_t", 50)
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

    def _render_plot_sets(self, ax, plot_sets: Dict[str, PlotSet]):
        """
        Completely subclass the data rendering logic of the superclass()
        In this case we're not directly plotting photometric data,
        instead we'll do SED analysis and then plot the resulting data.
        """
        # we are interested in the B and V band data (TODO: remove hard coding later)
        b_set = plot_sets["2019-AAVSO/nominal/B"]
        v_set = plot_sets["2019-AAVSO/nominal/V"]

        # Loop through time, sampling the apparent mag of the fit for each set
        # From this we calculate the absolute mag (from V band) and the observed color (B-V)
        abs_mag = []
        b_v_obs = []
        b_v_int = []
        delta_ts = np.append(np.arange(0.1, 2.0, 0.1), np.arange(2.0, self._max_delta_t, 0.5))
        for delta_t in delta_ts:
            log_delta_t = np.log10(delta_t)
            b = b_set.fits.find_y_value(log_delta_t)
            v = v_set.fits.find_y_value(log_delta_t)
            if b is not None and v is not None:
                bv = b - v
                b_v_obs.append(bv)
                b_v_int.append(bv - self._e_bv)
                abs_mag.append(v - self._mu)

        color = "b"
        ax.errorbar(unumpy.nominal_values(b_v_int), unumpy.nominal_values(abs_mag),
                    xerr=unumpy.std_devs(b_v_int), yerr=unumpy.std_devs(abs_mag),
                    label="From fits", fmt="D", color=color, fillstyle='full', markersize=self._marker_size * 2,
                    capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)

        # Now let's look at the underlying data and compare measurements
        # TODO: look to do this without interacting with the PlotSet's df directly
        b_df = b_set.df
        v_df = v_set.df
        b_df["r_day"] = np.round(b_df["day"], 3)
        v_df["r_day"] = np.round(v_df["day"], 3)
        df_join = b_df.drop_duplicates(subset="r_day").set_index("r_day")\
            .join(v_df.drop_duplicates(subset="r_day").set_index("r_day"), on="r_day", how="inner", lsuffix="_b", rsuffix="_v", sort="b_day")\
            .query(F"r_day <= {self._max_delta_t}")

        b_v_obs, b_v_obs_err = ColorMagnitudePlot._subtract_with_err(df_join["mag_b"], df_join["mag_v"], df_join["mag_err_b"], df_join["mag_err_v"])
        b_v_int, b_v_int_err = ColorMagnitudePlot._subtract_with_err(b_v_obs, self._e_bv.nominal_value, b_v_obs_err, self._e_bv.std_dev)
        abs_mag, abs_mag_err = ColorMagnitudePlot._subtract_with_err(df_join["mag_v"], self._mu.nominal_value, df_join["mag_err_v"], self._mu.std_dev)

        color = "darkred"
        ax.errorbar(b_v_int, abs_mag, xerr=b_v_int_err, yerr=abs_mag_err,
                    label="AAVSO measurements", fmt="o", color=color, fillstyle='full', markersize=self._marker_size * 2,
                    capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)
        return

    @classmethod
    def _subtract_with_err(cls, val1, val2, err1=None, err2=None):
        nominal = np.subtract(val1, val2)
        if err1 is not None and err2 is not None:
            err = np.sqrt(np.add(np.power(err1, 2), np.power(err2, 2)))
        elif err1 is None:
            err = err2
        elif err2 is None:
            err = err1
        else:
            err = None
        return nominal, err
