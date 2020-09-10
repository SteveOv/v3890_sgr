from uncertainties import ufloat_fromstr, UFloat
from plot.BasePlot import *
from fitting import FitSet, Lightcurve
from utility import uncertainty_math as um, colors
from numpy import ndarray


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
        self._default_max_delta_t = 70
        return

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
        delta_ts = np.append(np.arange(0.1, 2.0, 0.1), np.arange(2.0, self.max_delta_t, 0.5))

        # Could be fit set and/or lightcurve data
        for data_set in [kwargs["fit_sets"], kwargs["lightcurves"]]:

            # we are interested in the B and V band fits data.  May be more than one of each.
            if data_set is not None and len(data_set):
                b_sets = ColorMagnitudePlot._values_with_key_ends_with(data_set, "B-band")
                v_sets = ColorMagnitudePlot._values_with_key_ends_with(data_set, "V-band")

                for b_set, v_set in zip(b_sets, v_sets):
                    e_b_v = ufloat_fromstr(b_set.metadata.get_or_default("E(B-V)", None))
                    mu = ufloat_fromstr(b_set.metadata.get_or_default("mu", None))
                    marker = b_set.metadata.get_or_default("marker", "D")

                    if isinstance(b_set, FitSet):
                        dt, b_v_int, b_v_int_err, abs_mag, abs_mag_err = \
                            self.__class__._calculate_color_magnitudes_from_fit_sets(b_set, v_set, delta_ts,
                                                                                     e_b_v, mu)
                    else:
                        dt, b_v_int, b_v_int_err, abs_mag, abs_mag_err = \
                            self.__class__._calculate_color_magnitudes_from_lightcurves(b_set, v_set, delta_ts,
                                                                                        e_b_v, mu)

                    label = b_set.metadata.get_or_default("label", f"E(B-V)={e_b_v.nominal_value:.2f}\n$\\mu$={mu.nominal_value:.2f}")
                    self._draw_color_magnitude_plot(ax, dt, b_v_int, b_v_int_err, abs_mag, abs_mag_err,
                                                    label=label, marker=marker)

        return

    def _draw_color_magnitude_plot(self, ax: Axes, delta_t, intrinsic_color, intrinsic_color_err, mag, mag_err,
                                   label: str, color: str = "k", marker: str = "D"):
        # TODO: support changing the color of the plotted points on delta_t
        for dt, a_color, a_color_err, a_mag, a_mag_err in \
                zip(delta_t, intrinsic_color, intrinsic_color_err, mag, mag_err):
            # We use the fill color to highlight the passing of time - that why we plot individually
            if dt < 6:
                fillcolor = "cyan"
            elif dt < 15:
                fillcolor = "w"
            elif dt < 25:
                fillcolor = "y"
            else:
                fillcolor = "r"

            ax.errorbar(x=a_color, y=a_mag,
                        # xerr=intrinsic_color_err, yerr=mag_err,
                        label=label,
                        fmt=marker, mfc=fillcolor, color=color, fillstyle='none', markersize=self.marker_size * 10,
                        capsize=1, ecolor=color, elinewidth=self.line_width / 2,
                        linewidth=self.line_width / 4, alpha=self.alpha, zorder=1)

            # Only spec the label once
            label = None
        return

    @classmethod
    def _calculate_color_magnitudes_from_fit_sets(cls, b_set: FitSet, v_set: FitSet,
                                                  delta_ts: [float], color_excess: UFloat, mu: UFloat):
        """
        Calculate the (intrinsic)color v (absolute)magnitude data based on the passed lightcurve B & V fits
        """
        # Loop through time, sampling the apparent mag of the fit for each set
        mag_b = list()
        mag_b_err = list()
        mag_v = list()
        mag_v_err = list()
        for delta_t in delta_ts:
            # These will be ufloats - long term intention is to get rid of these but for now work around them
            B = b_set.find_y_value(delta_t)
            V = v_set.find_y_value(delta_t)
            if B is not None and V is not None:
                mag_b.append(B.nominal_value)
                mag_b_err.append(B.std_dev)
                mag_v.append(V.nominal_value)
                mag_v_err.append(V.std_dev)

        # From this we calculate the observed color, intrinsic color & absolute mag (from V band)
        b_v_obs, b_v_obs_err = colors.color_from_magnitudes(mag_b, mag_b_err, mag_v, mag_v_err)
        b_v_int, b_v_int_err = colors.intrinsic_color_from_observed_color_and_excess(b_v_obs.tolist(),
                                                                                     b_v_obs_err.tolist(),
                                                                                     color_excess.nominal_value,
                                                                                     color_excess.std_dev)

        abs_mag, abs_mag_err = cls._calculate_absolute_mag(mag_v, mag_v_err, mu.nominal_value, mu.std_dev)

        return delta_ts, b_v_int, b_v_int_err, abs_mag, abs_mag_err

    @classmethod
    def _calculate_color_magnitudes_from_lightcurves(cls, b_lc: Lightcurve, v_lc: Lightcurve,
                                                     delta_ts: [float], color_excess: UFloat, mu: UFloat):
        """
        Calculate the (intrinsic)color and (absolute)magnitude data based on the passed B & V lightcurve data
        """
        b_df = b_lc.df.copy()
        v_df = v_lc.df.copy()

        # Join up the B and V data on matching day value (with specified sig figs).
        # This then allows us to treat it as tabular data and use the same processing logic as for the fits.
        b_df["r_day"] = np.round(b_df["day"], 2)
        v_df["r_day"] = np.round(v_df["day"], 2)
        df_join = b_df.drop_duplicates(subset="r_day").set_index("r_day")\
            .join(v_df.drop_duplicates(subset="r_day").set_index("r_day"), on="r_day", how="inner", lsuffix="_b", rsuffix="_v", sort="b_day")\
            .query(F"(r_day <= {max(delta_ts)})")

        # The above is generating some complex query logic within pandas.  We get a "truth value ambiguous" error
        # when trying to do maths on the results as columns (as series), so convert them to lists first.
        b_v_obs, b_v_obs_err = colors.color_from_magnitudes(df_join["mag_b"].tolist(), df_join["mag_err_b"].tolist(),
                                                            df_join["mag_v"].tolist(), df_join["mag_err_v"].tolist())
        b_v_int, b_v_int_err = colors.intrinsic_color_from_observed_color_and_excess(b_v_obs.tolist(),
                                                                                     b_v_obs_err.tolist(),
                                                                                     color_excess.nominal_value,
                                                                                     color_excess.std_dev)

        abs_mag, abs_mag_err = cls._calculate_absolute_mag(df_join["mag_v"].tolist(), df_join["mag_err_v"].tolist(),
                                                           mu.nominal_value, mu.std_dev)

        return df_join["day_b"].tolist(), b_v_int, b_v_int_err, abs_mag, abs_mag_err

    @classmethod
    def _calculate_absolute_mag(cls, mag_v, mag_v_err, mu, mu_err):
        """
        Calculate the absolute magnitude from the distance modulus.
        Based on
            mu = mag(apparent) - mag(absolute)
        therefore
            mag(absolute) = mag(apparent) - mu
        """
        # Get the distance modulus into the same form as the V magnitude.
        dist_mod = np.full_like(mag_v, mu).tolist() if isinstance(mag_v, ndarray) else mu
        dist_mod_err = np.full_like(mag_v_err, mu_err).tolist() if isinstance(mag_v_err, ndarray) else mu_err
        return um.subtract(mag_v, mag_v_err, dist_mod, dist_mod_err)

    @classmethod
    def _values_with_key_ends_with(cls, dc: Dict, key_end: str) -> List:
        return [v for k, v in dc.items() if k.endswith(key_end)]
