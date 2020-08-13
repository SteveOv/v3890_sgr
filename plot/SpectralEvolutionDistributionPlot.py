import math
from uncertainties import ufloat_fromstr, UFloat
from utility import math_uncertainties as unc
from plot.TimePlotSupportingLogAxes import *


class SpectralEvolutionDistributionPlot(TimePlotSupportingLogAxes):

    _mag_ab_correction_factor = {
        # FROM LJMU Website
        "B": -0.1,
        "V": 0,
        "R": 0.2,
        "I": 0.45,

        # From Breeveld 2010, Swift-UVOT-CALDDB-16-R01
        "UVM2": 1.69,
        "UVW2": 1.73
    }

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=True)

        # Override the most basic behaviour - we need a large plot with labelling of data points, so no legend
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_show_legend = False

        # log(luminosity) scale derived from the flux density and distance.
        self._default_y_label = "$\\log(L_{\\nu})$ [Jy m$^2$]"
        # super() doesn't restrict the y-axis, so we implement these properties here
        self._default_y_lim_log = (1e38, 3e43)
        self._default_y_ticks_log = [1e39, 1e40, 1e41, 1e42, 1e43]
        self._default_y_tick_labels_log = ["39", "40", "41", "42", "43"]

        # x-axis always on a log scale - set the defaults for the super() to configure from
        self._default_x_label = "$\\log(\\nu)$ [Hz]"
        self._default_x_lim_log = (10**14.5, 10**15.3)
        self._default_x_ticks_log = [10**14.6, 10**14.7, 10**14.8, 10**14.9, 10**15.0, 10**15.1, 10**15.2, 10**15.3]
        self._default_x_tick_labels_log = ["14.6", "14.7", "14.8", "14.9", "15.0", "15.1", "15.2", "15.3"]

        # TODO: 2nd y-axis in magnitudes - same scale as y so we will need to convert
        self._default_y2_label = "$\\text{m_V}$"
        self._default_y2_lim = [0, 25]
        self._default_y2_scale_log = False
        self._default_y2_lim_log = [0.01, 25]
        self._default_y2_ticks_log = [1, 10, 100]
        return

    @property
    def x_scale_log(self) -> bool:
        return True     # Override Super(): Always log

    @property
    def x_tick_labels(self) -> List[str]:
        return self._param("x_tick_labels", self._default_x_tick_labels_log)

    @property
    def y_scale_log(self) -> bool:
        return True     # Override Super(): Always log

    @property
    def y_lim(self) -> List[float]:
        return self._param("y_lim", self._default_y_lim_log)

    @property
    def y_ticks(self) -> List[float]:
        return self._param("y_ticks", self._default_y_ticks_log)

    @property
    def y_tick_labels(self) -> List[str]:
        return self._param("y_tick_labels", self._default_y_tick_labels_log)

    @property
    def target_distance_parsecs(self) -> UFloat:
        # Want a failure if the distance is not set correctly.
        return self._param("distance_pc", None)

    def _configure_ax(self, ax: Axes, **kwargs):
        # This looks after the basic/common setup of the shared x-axis and the primary y-axis
        super()._configure_ax(ax, **kwargs)

        # Super doesn't put any restrictions on y-axis, but we need them here.
        ax.set(xlim=self.x_lim, xticks=self.x_ticks, xticklabels=self.x_tick_labels)
        ax.set_xticks([], minor=True)  # For some reason matplotlib will add in some minor ticks/labels - remove them
        ax.set_yticks([], minor=True)
        ax.set(ylim=self.y_lim, yticks=self.y_ticks, yticklabels=self.y_tick_labels)
        ax.grid(which="minor", linestyle="none")
        ax.grid(which="major", linestyle="none")

        # Now we set up the secondary y-axis on magnitude scale
        # TODO: will need to show values equivalent to the y-axis so maybe we use same scale but label differently
        """
        self._ax2 = ax.twinx()
        self._ax2.set_ylabel(self._param("y2_label", self._default_y2_label))

        y2_scale_log = self._param("y2_scale_log", self._default_y2_scale_log)
        if y2_scale_log:
            self._ax2.set_yscale("log")
            self._ax2.set_yticks(self._param("y2_ticks_log", self._default_y2_ticks_log), minor=False)
            self._ax2.set_yticklabels(self._param("y2_ticks_log", self._default_y2_ticks_log), minor=False)
            self._ax2.set(ylim=self._param("y2_lim", self._default_y2_lim_log))
        else:
            self._ax2.set(ylim=self._param("y2_lim", self._default_y2_lim_linear))
        """
        return

    def _draw_plot_sets(self, ax: Axes, plot_sets: Dict[str, PlotSet]):
        """
        Completely subclass the data rendering logic of the superclass()
        In this case we're not directly plotting photometric data,
        instead we'll do SED analysis and then plot the resulting data.
        """
        delta_ts = self._param("delta_t", [1, 2, 3, 5, 10, 20])
        nu_effs = self._param(
            "nu_eff", {"I": 3.72e14, "R": 4.556e14, "V": 5.441e14, "B": 6.737e14, "UVM2": 1.335e15, "UVW2": 1.555e15})

        r_m, r_m_err = unc.multiply(self.target_distance_parsecs.nominal_value, 3.086e16,
                                    self.target_distance_parsecs.std_dev, 0)

        # This is an interim step - parses the source data and calculates flux & luminosity fields
        # We don't include the distance uncertainty in the calculations as it's systematic.
        # Instead we'll work it out once and present it separately.
        df = self.__class__._calculate_sed_data(plot_sets, nu_effs, delta_ts, r_m, distance_m_err=0)

        ix = 0
        for delta_t in sorted(delta_ts):
            # Plot the error bars of the points
            dt_df = df.query(f"delta_t == {delta_t}").sort_values(by="nu_eff")
            self._plot_df_to_error_bars_on_ax(ax, dt_df, "nu_eff", "L_nu", "L_nu_err", "k", fmt=",")
            self._plot_df_to_lines_on_ax(ax, dt_df, "nu_eff", "L_nu", "k")

            last_good_band = dt_df.query("L_nu>0").iloc[-1]
            x_pos_eol = last_good_band["nu_eff"] + 10**13
            y_pos = last_good_band["L_nu"]
            # TODO: specific to this plot, handle a crush
            if ix == 5:
                y_pos -= 3e39

            # Annotate the Delta t at the right end of each line
            label = f"$\\Delta t={delta_t:.2f}$" if delta_t != int(delta_t) else f"$\\Delta t={delta_t}$"
            ax.annotate(label, xycoords="data", xy=(x_pos_eol, y_pos))
            ix += 1

        # Now annotate the bands - along the top for now
        y_pos = self.y_ticks[-1]
        for band in nu_effs:
            ax.annotate(band, xycoords="data", xy=(nu_effs[band], y_pos), horizontalalignment="center")

        # Add a single point, but with the distance uncertainty so that we have a representation
        # of the systematic distance error.  Get a flux density for a luminosity of 10^39.
        # Then put it back into the luminosity calculation, but with the distance uncertainty and plot the result.
        x_pos = nu_effs["I"]
        y_pos = 2e38
        f_nu, f_nu_err = unc.divide(y_pos, 4 * math.pi * np.power(r_m, 2))
        lum_nu, lum_nu_err = \
            self.__class__._calculate_specific_luminosity_for_flux_and_distance(f_nu, f_nu_err, r_m, r_m_err)
        self._plot_points_to_error_bars_on_ax(ax, [x_pos], [lum_nu], [lum_nu_err], "k", fmt=",")
        ax.annotate("Distance uncertainty", xycoords="data", xy=(x_pos + 10**13, y_pos - 2e37))
        return

    @classmethod
    def _calculate_sed_data(cls, plot_sets: Dict[str, PlotSet],
                            nu_eff_lookup: Dict, delta_ts: Dict,
                            distance_m: float, distance_m_err: float=0) -> DataFrame:

        df = cls._get_magnitudes_from_photometric_fits(plot_sets, nu_eff_lookup, delta_ts)

        # TODO: extinction correction.

        # Calculate flux density values for the retrieved data.
        df[['flux_hz', "flux_hz_err"]] = df.apply(
            lambda d: cls._calculate_flux_density_for_magnitude_and_band(d["mag"], d["mag_err"], d["band"]),
            axis=1,
            result_type="expand")

        # Calculate the specific luminosity from the flux density
        df[["L_nu", "L_nu_err"]] = df.apply(
            lambda d: cls._calculate_specific_luminosity_for_flux_and_distance(
                d["flux_hz"], d["flux_hz_err"], distance_m, distance_m_err), axis=1, result_type="expand")
        return df

    @classmethod
    def _get_magnitudes_from_photometric_fits(cls, plot_sets: Dict[str, PlotSet],
                                              nu_eff_lookup: Dict, delta_ts: Dict) -> DataFrame:
        rows = []
        for plot_set_key in plot_sets:
            plot_set = plot_sets[plot_set_key]
            band = plot_set.param("set")
            label = plot_set.label

            # Now use the fits to calculate magnitudes at the requested time intervals
            for delta_t in delta_ts:
                mag = plot_set.fits.find_y_value(delta_t)
                if mag is not None:
                    rows.append({"band": band, "nu_eff": nu_eff_lookup[band],
                                 "label": label, "delta_t": delta_t, "mag": mag.nominal_value, "mag_err": mag.std_dev})

        if len(rows) > 0:
            df = DataFrame.from_records(rows, columns=rows[0].keys())
        else:
            df = None
        return df

    @classmethod
    def _calculate_flux_density_for_magnitude_and_band(cls, mag, mag_err, band):
        """
        Calculate the flux density from the passed magnitude.
        """
        #
        # f_nu = 10 ^ 0.4(8.9 - m_AB)
        #
        # Based on the relation: m_AB = -2.5 log(f_nu) + 8.9
        # https://www.astro.ljmu.ac.uk/~ikb/convert-units/node1.html
        #
        m_ab, m_ab_err = unc.add(mag, cls._mag_ab_correction_factor[band], mag_err, 0)
        m_int, m_int_err = unc.subtract(8.9, m_ab, 0, m_ab_err)
        exponent, exponent_err = unc.multiply(0.4, m_int, 0, m_int_err)
        f_nu, f_nu_err = unc.power(10, exponent, 0, exponent_err)
        return f_nu, f_nu_err

    @classmethod
    def _calculate_specific_luminosity_for_flux_and_distance(cls, flux, flux_err, distance_m, distance_m_err=0):
        """
        Calculate the specific luminosity based on the passed flux density and distance (in metres)
        using the relation: L_nu = 4pi * r^2 * F_nu
        """
        # Calculate the luminosity L_nu = 4pi * r^2 * F_nu
        a, a_err = unc.multiply(flux, 4*math.pi, flux_err, 0)
        r2, r2_err = unc.power(distance_m, 2, distance_m_err, 0)
        l_nu, l_nu_err = unc.multiply(a, r2, a_err, r2_err)
        return l_nu, l_nu_err
