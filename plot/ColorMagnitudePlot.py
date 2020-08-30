from uncertainties import unumpy, ufloat_fromstr, UFloat
from plot.BasePlot import *
from fitting import FitSet, Lightcurve
from utility import uncertainty_math as um
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
        self._default_mu = self._default_color_excess = None
        self._default_max_delta_t = 70
        return

    @property
    def mu(self):
        return self._param("mu", self._default_mu)

    @property
    def color_excess(self) -> UFloat:
        return self._param("E(B-V)", self._default_color_excess)

    @property
    def comp_mu(self) -> UFloat:
        return ufloat_fromstr(self._param("comp_mu", "18.9+/-0"))

    @property
    def comp_color_excess(self) -> UFloat:
        return ufloat_fromstr(self._param("comp_E(B-V)", "1.0+/-0.2"))

    @property
    def comp_source(self) -> str:
        return self._param("comp_source", "lightcurves")

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
        # we are interested in the B and V band fits data
        fit_sets = kwargs["fit_sets"]
        delta_ts = np.append(np.arange(0.1, 2.0, 0.1), np.arange(2.0, self.max_delta_t, 0.5))

        def _value_on_key_ends_with(dc: Dict, key_end: str):
            return next(v for k, v in dc.items() if k.endswith(key_end)) if dc is not None else None
        b_set = _value_on_key_ends_with(fit_sets, "B-band")
        v_set = _value_on_key_ends_with(fit_sets, "V-band")

        # Get the color and magnitude data from the fitset data
        x_data, x_date_err, y_data, y_data_err = \
            self.__class__._calculate_color_magnitudes_from_fit_sets(b_set, v_set, delta_ts, self.color_excess, self.mu)

        color = "b"
        label = f"E(B-V)={self.color_excess.nominal_value:.2f}, $\\mu$={self.mu.nominal_value:.2f}"
        ax.errorbar(x_data, y_data,
                    # xerr=x_data_err, yerr=y_data_err,
                    label=label, fmt="D", color=color, fillstyle='full', markersize=self._marker_size * 2,
                    capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)

        if self.comp_source is not None and self.comp_source in kwargs:
            # If we have a comparison data set configured get the data - it's probably lightcurve data
            comp = kwargs[self.comp_source]
            b_set = _value_on_key_ends_with(comp, "B-band")
            v_set = _value_on_key_ends_with(comp, "V-band")
            x_data, x_date_err, y_data, y_data_err = \
                self.__class__._calculate_color_magnitudes_from_lightcurves(b_set, v_set, delta_ts,
                                                                            self.comp_color_excess, self.comp_mu)
            color = "r"
            label = f"E(B-V)={self.comp_color_excess.nominal_value:.2f}, $\\mu$={self.comp_mu.nominal_value:.2f}"
            ax.errorbar(x_data, y_data,
                        # xerr=x_data_err, yerr=y_data_err,
                        label=label, fmt="D", color=color, fillstyle='full', markersize=self._marker_size * 2,
                        capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)
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

        # From this we calculate the absolute mag (from V band) and the observed color (B-V)
        b_v_int, b_v_int_err = cls._calculate_intrinsic_color(mag_b, mag_b_err, mag_v, mag_v_err,
                                                              color_excess.nominal_value, color_excess.std_dev)

        abs_mag, abs_mag_err = cls._calculate_absolute_mag(mag_v, mag_v_err, mu.nominal_value, mu.std_dev)

        return b_v_int, b_v_int_err, abs_mag, abs_mag_err

    @classmethod
    def _calculate_color_magnitudes_from_lightcurves(cls, b_lc: Lightcurve, v_lc: Lightcurve,
                                                     delta_ts: [float], color_excess: UFloat, mu: UFloat):
        """
        Calculate the (intrinsic)color and (absolute)magnitude data based on the passed B & V lightcurve data
        """
        b_df = b_lc.df.copy()
        v_df = v_lc.df.copy()

        b_df["r_day"] = np.round(b_df["day"], 3)
        v_df["r_day"] = np.round(v_df["day"], 3)
        df_join = b_df.drop_duplicates(subset="r_day").set_index("r_day")\
            .join(v_df.drop_duplicates(subset="r_day").set_index("r_day"), on="r_day", how="inner", lsuffix="_b", rsuffix="_v", sort="b_day")\
            .query(F"r_day <= {max(delta_ts)}")

        b_v_int, b_v_int_err = cls._calculate_intrinsic_color(df_join["mag_b"].tolist(), df_join["mag_err_b"].tolist(),
                                                              df_join["mag_v"].tolist(), df_join["mag_err_v"].tolist(),
                                                              color_excess.nominal_value, color_excess.std_dev)

        abs_mag, abs_mag_err = cls._calculate_absolute_mag(df_join["mag_v"].tolist(), df_join["mag_err_v"].tolist(),
                                                           mu.nominal_value, mu.std_dev)

        return b_v_int, b_v_int_err, abs_mag, abs_mag_err

    @classmethod
    def _calculate_intrinsic_color(cls, mag_b, mag_b_err, mag_v, mag_v_err, color_excess, color_excess_err):
        b_v_obs, b_v_obs_err = um.subtract(mag_b, mag_b_err, mag_v, mag_v_err)

        if isinstance(b_v_obs, ndarray):
            # Handle multiple data.  Get the color excess into array form too
            color_excess = np.full_like(b_v_obs, color_excess).tolist()
            color_excess_err = np.full_like(b_v_obs, color_excess_err).tolist()
            b_v_int, b_v_int_err = um.subtract(b_v_obs.tolist(), b_v_obs_err.tolist(), color_excess, color_excess_err)
            b_v_int = b_v_int.tolist()
            b_v_int_err = b_v_int_err.tolist()
        else:
            b_v_int, b_v_int_err = um.subtract(b_v_obs, b_v_obs_err, color_excess, color_excess_err)

        return b_v_int, b_v_int_err

    @classmethod
    def _calculate_absolute_mag(cls, mag_v, mag_v_err, mu, mu_err):
        # Get the distance modulus into the same form as the V magnitude.
        dist_mod = np.full_like(mag_v, mu).tolist() if isinstance(mag_v, ndarray) else mu
        dist_mod_err = np.full_like(mag_v_err, mu_err).tolist() if isinstance(mag_v_err, ndarray) else mu_err
        return um.subtract(mag_v, mag_v_err, dist_mod, dist_mod_err)
