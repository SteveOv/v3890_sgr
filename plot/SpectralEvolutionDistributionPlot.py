import math
from typing import List, Dict, Tuple
from uncertainties import UFloat
from utility import uncertainty_math as unc, magnitudes as mag
from plot.BasePlot import *


class SpectralEvolutionDistributionPlot(BasePlot):

    """
    _mag_ab_correction_factors = {
        # FROM LJMU Website
        "B": -0.1,
        "V": 0,
        "R": 0.2,
        "I": 0.45,

        # From Breeveld (2010) Swift-UVOT-CALDDB-16-R01
        "UVM2": 1.69,
        "UVW2": 1.73
    }
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        # Override the most basic behaviour - we need a large plot with labelling of data points, so no legend
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_show_legend = False

        # log(luminosity) scale derived from the flux density and distance.
        self._default_y_label = "$\\log(L_{\\nu})$ [Jy m$^2$]"

        # super() doesn't restrict the y-axis, so we implement these properties here
        self._default_y_lim = (1e38, 3e44)
        self._default_y_ticks = [1e39, 1e40, 1e41, 1e42, 1e43, 1e44]
        self._default_y_tick_labels = ["39", "40", "41", "42", "43", "44"]

        # x-axis always on a log scale - set the defaults for the super() to configure from
        self._default_x_label = "$\\log(\\nu)$ [Hz]"
        self._default_x_lim = (10**14.5, 10**15.3)
        self._default_x_ticks = [10**14.6, 10**14.7, 10**14.8, 10**14.9, 10**15.0, 10**15.1, 10**15.2, 10**15.3]
        self._default_x_tick_labels = ["14.6", "14.7", "14.8", "14.9", "15.0", "15.1", "15.2", "15.3"]

        self._default_delta_t = [1, 2, 3, 5, 10, 20]

        # UVM2, UVW2 values from Breeveld (2010) Swift-UVOT-CALDDB-16-R01
        self._default_lambda_effs = \
            {"I": 7970e-10, "R": 6380e-10, "V": 5450e-10, "B": 4360e-10, "UVM2": 2221e-10, "UVW2": 1991e-10}

        # From Schlegel et al. (1998) Table 6, pp 551 A/A_V values for CTIO B, V, R & I filters (CCD Cousins)
        # UVM2, UVW2 from Darnley et al. (2016) & private conversation
        self._default_relative_extinction_coeffs = \
            {"I": 0.601, "R": 0.807, "V": 0.992, "B": 1.324, "UVM2": 1.968, "UVW2": 1.968}

        # These are derived data which is not directly specified in params.
        self._zero_mag_fluxes = self.__class__._calculate_zero_mag_fluxes()
        e_b_v = self.color_excess
        self._extinction_corrections = self.__class__._calculate_extinction_corrections(
            self.relative_extinction_coeffs, e_b_v.nominal_value, e_b_v.std_dev)
        return

    @property
    def x_tick_labels(self) -> List[str]:
        return self._param("x_tick_labels", self._default_x_tick_labels)

    @property
    def y_lim(self) -> List[float]:
        return self._param("y_lim", self._default_y_lim)

    @property
    def y_ticks(self) -> List[float]:
        return self._param("y_ticks", self._default_y_ticks)

    @property
    def y_tick_labels(self) -> List[str]:
        return self._param("y_tick_labels", self._default_y_tick_labels)

    @property
    def delta_t(self) -> List[float]:
        return self._param("delta_t", self._default_delta_t)

    @property
    def target_distance_pc(self) -> UFloat:
        # Want a failure if the distance is not set correctly.
        return self._param("distance_pc", None)

    @property
    def target_distance_m(self) -> Tuple[float, float]:
        r_pc = self.target_distance_pc
        return unc.multiply(r_pc.nominal_value, r_pc.std_dev, 3.086e16, 0)

    @property
    def color_excess(self) -> UFloat:
        return self._param("E(B-V)", None)

    @property
    def lambda_effs(self) -> Dict[str, float]:
        return self._param("lambda_effs", self._default_lambda_effs)

    @property
    def relative_extinction_coeffs(self) -> Dict[str, float]:
        """
        Extinction in various bands as expressed by r_e = A/E(B-V).  So A = r_e * E(B-V)
        """
        return self._param("relative_extinction_coeffs", self._default_relative_extinction_coeffs)

    def _configure_ax(self, ax: Axes, **kwargs):
        # This looks after the basic/common setup of the shared x-axis and the primary y-axis
        super()._configure_ax(ax, **kwargs)

        # Super doesn't do log axes, so we deal with that here.  Redo ticks as they get lost when we change to log
        ax.set_xscale("log")
        ax.set(xlim=self.x_lim, xticks=self.x_ticks, xticklabels=self.x_tick_labels)
        ax.set_xticks([], minor=True)  # For some reason matplotlib will add in some minor ticks/labels - remove them

        # Super doesn't put any restrictions on y-axis, but we need them here.
        ax.set_yscale("log")
        ax.set_yticks([], minor=True)
        ax.set(ylim=self.y_lim, yticks=self.y_ticks, yticklabels=self.y_tick_labels)

        ax.grid(which="minor", linestyle="none")
        ax.grid(which="major", linestyle="none")
        return

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        The call from super() to get this plot to draw its content to the Axes. In this case we're not directly
        plotting photometric data, instead we'll do SED analysis from fits and then plot the resulting data.
        """
        fit_sets = kwargs["fit_sets"]
        r_m, r_m_err = self.target_distance_m

        nu_effs = self.__class__._calculate_effective_frequencies(self.lambda_effs)
        ext_corrections = self.__class__._calculate_extinction_corrections(self.relative_extinction_coeffs,
                                                                           self.color_excess.nominal_value,
                                                                           self.color_excess.std_dev,
                                                                           R_V=3.1)

        # We don't include the distance uncertainty in these SED calculations as it's systematic.
        # Instead we'll work it out once and present it separately.
        df = self.__class__._calculate_sed_data(fit_sets, self.delta_t, nu_effs, ext_corrections, self._zero_mag_fluxes, r_m)

        ix = 0
        for delta_t in sorted(self.delta_t):
            # Plot the error bars of the points
            dt_df = df.query(f"delta_t == {delta_t}").sort_values(by="nu_eff")
            self._plot_df_to_error_bars_on_ax(ax, dt_df, "nu_eff", "L_nu", "L_nu_err", "k", fmt=",")
            self._plot_df_to_lines_on_ax(ax, dt_df, "nu_eff", "L_nu", "k")

            last_good_band = dt_df.query("L_nu>0").iloc[-1]
            x_pos_eol = last_good_band["nu_eff"] + 10 ** 13
            y_pos = last_good_band["L_nu"]
            # Specific to this plot, handle a crush
            if ix == 5:
                y_pos -= 3e41

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
        y_pos = 8e38
        f_nu, f_nu_err = unc.divide(y_pos, 0, 4 * math.pi * np.power(r_m, 2), 0)
        lum_nu, lum_nu_err = \
            self.__class__._calculate_specific_luminosity(f_nu, f_nu_err, r_m, r_m_err)
        self._plot_points_to_error_bars_on_ax(ax, [x_pos], [lum_nu], [lum_nu_err], "k", fmt=",")
        ax.annotate("Distance uncertainty", xycoords="data", xy=(x_pos + 10 ** 13, 4e38))
        return

    @classmethod
    def _calculate_sed_data(cls, fit_sets: Dict, delta_ts: [],
                            nu_eff_lookup: Dict, extinction_corrections: Dict, band_zero_mag_fluxes: Dict,
                            distance_m: float, distance_m_err: float = 0) -> DataFrame:

        # Generate the dataframe with bands, and (extinction corrected) magnitudes at the requested times
        df = cls._get_magnitudes_from_photometric_fits(fit_sets, nu_eff_lookup, extinction_corrections, delta_ts)

        # Calculate flux density values for the retrieved, corrected magnitudes.
        df[['flux_hz', "flux_hz_err"]] = df.apply(
            lambda d: cls._calculate_flux_density(d["mag"], d["mag_err"], d["band"], band_zero_mag_fluxes),
            axis=1,
            result_type="expand")

        # Calculate the specific luminosity from the flux density
        df[["L_nu", "L_nu_err"]] = df.apply(
            lambda d: cls._calculate_specific_luminosity(
                d["flux_hz"], d["flux_hz_err"], distance_m, distance_m_err), axis=1, result_type="expand")
        return df

    @classmethod
    def _get_magnitudes_from_photometric_fits(cls, fit_sets: Dict,
                                              nu_eff_lookup: Dict, ext_corrections: Dict, delta_ts: []) -> DataFrame:
        """
        Generates a data frame from the passed plot_set fitted light-curves,
        containing the magnitudes and extinction magnitudes for the bands and times requested.
        """
        rows = []
        for fit_set_key, fit_set in fit_sets.items():
            label = fit_set.label
            band = fit_set.metadata.get_or_default("band", label)

            # Now use the fits to calculate magnitudes at the requested time intervals
            for delta_t in delta_ts:
                mag = fit_set.find_y_value(delta_t)
                if mag is not None:
                    # Calculate the corrected mag too - subtract the extinction correction.
                    cor_mag, cor_mag_err = \
                        cls._correct_magnitudes(mag.nominal_value, mag.std_dev, band, ext_corrections)

                    rows.append({"band": band, "nu_eff": nu_eff_lookup[band],
                                 "label": label, "delta_t": delta_t,
                                 "mag": cor_mag, "mag_err": cor_mag_err})

        if len(rows) > 0:
            df = DataFrame.from_records(rows, columns=rows[0].keys())
        else:
            df = None
        return df

    @classmethod
    def _calculate_flux_density(cls, mag: float, mag_err: float, band: str, zero_mag_fluxes: Dict[str, float]) \
            -> Tuple[float, float]:
        """
        Calculate the flux density [Jy] from the passed magnitude
        based on the band and the band specific zero magnitude flux.
        """
        #
        # Based on the flux ratio; m_1 - m_2 = -2.5 log(f_1 / f_2)
        # where
        #           m_2 = 0
        #           f_2 = f_0 = flux at mag zero for the band
        # therefore
        #           f_nu = 10^(-0.4 * mag) * f_0
        #
        exponent, exponent_err = unc.multiply(-0.4, 0, mag, mag_err)
        f_int, f_int_err = unc.power(10, 0, exponent, exponent_err)
        f_nu, f_nu_err = unc.multiply(f_int, f_int_err, zero_mag_fluxes[band], 0)
        return f_nu, f_nu_err

    @classmethod
    def _calculate_specific_luminosity(cls, flux: float, flux_err: float, distance_m: float, distance_m_err: float = 0) \
            -> Tuple[float, float]:
        """
        Calculate the specific luminosity based on the passed flux density and distance (in metres)
        using the relation: L_nu = 4pi * r^2 * F_nu
        """
        # Calculate the luminosity L_nu = 4pi * r^2 * F_nu
        a, a_err = unc.multiply(flux, flux_err, 4*math.pi, 0)
        r2, r2_err = unc.power(distance_m, distance_m_err, 2, 0)
        l_nu, l_nu_err = unc.multiply(a, a_err, r2, r2_err)
        return l_nu, l_nu_err

    @classmethod
    def _calculate_effective_frequencies(cls, lambda_eff: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate central frequency from wavelengths based on; c= lambda * freq --> freq = c / lambda
        """
        nu_eff = {}
        for key in lambda_eff:
            nu_eff[key] = 2.998e8 / lambda_eff[key]
        return nu_eff

    @classmethod
    def _calculate_zero_mag_fluxes(cls) -> Dict[str, float]:
        """
        Calculate the band specific 0 mag(Vega) flux densities [Jy] from the passed mag(AB) - mag Vega factors.
        """
        # mag(AB) = corr, where mag(Vega) == 0
        band_zero_fluxes = {}
        for band in mag.mag_ab_correction_factors:
            band_zero_fluxes[band], _ = mag.flux_density_jy_from_mag_ab(mag.mag_ab_correction_factors[band], 0)
        return band_zero_fluxes

    @classmethod
    def _calculate_extinction_corrections(cls, coefficients: Dict[str, float], color_excess: float,
                                          color_excess_err: float, R_V: float = 3.1) -> Dict[str, Tuple[float, float]]:
        """
        The extinction correction in magnitudes [as from Schaefer (2010) Section 17]) for each band
                A = [A/A(V)] * R_V * E(B-V)
        """
        extinction_for_bands = {}
        for band in coefficients:
            correction, correction_err = unc.multiply((coefficients[band] * R_V), 0, color_excess, color_excess_err)
            extinction_for_bands[band] = (correction, correction_err)
        return extinction_for_bands

    @classmethod
    def _correct_magnitudes(cls, mag, mag_err, band: str, corrections: Dict[str, Tuple[float, float]]):
        correction, correction_err = corrections[band]
        return unc.subtract(mag, mag_err, correction, correction_err)
