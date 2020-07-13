from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from plot import SinglePlotSupportingLogAxes, PlotSet


class SpectralEvolutionDistributionPlot(SinglePlotSupportingLogAxes):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=False)

        # Override the most basic behaviour - we need a large plot with labelling of data points, so no legend
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_show_legend = False

        self._default_x_scale_log = True
        self._default_y_scale_log = False
        self._default_x_axis = "frequency"

        self._y_label = "Apparent magnitude [mag]"
        self._y_lim = (5.8, 17)

        self._x_axis = self._param("x_axis", self._default_x_axis)
        if self._x_axis == self._default_x_axis:
            self._x_scale_log = True
            self._default_x_label = "$\\log(\\nu)$ [Hz]"
            self._default_x_lim_log = (np.log10(3.5e14), np.log10(2.0e15))
            self._default_x_ticks_log = [14.6, 14.7, 14.8, 14.9, 15.0, 15.1, 15.2, 15.3]
        else:
            self._x_scale_log = False
            self._default_x_lim = (100, 900)
            self._default_x_ticks = np.arange(200, 900, 200)
            self._default_x_label = "Wavelength [nm]"

        # TODO - need to set up second y-axis as L_x
        self._default_y2_label = "Count Rate (0.1 - 10 keV) [s$^{-1}$]"
        self._default_y2_lim = [0, 25]
        self._default_y2_scale_log = False
        self._default_y2_lim_log = [0.01, 25]
        self._default_y2_ticks_log = [1, 10, 100]
        return

    def _render_plot(self, plot_sets: Dict[str, PlotSet], title: str) -> plt.figure:

        x_axis = self._param("x_axis", self._default_x_axis)
        if x_axis == "frequency":
            self._default_x_scale_log = True
        else:
            self._default_x_scale_log = False
            self._default_x_label = "wavelength [nm]"

        return super()._render_plot(plot_sets, title)

    def _configure_ax(self, ax):
        # Invert the y-axis for magnitudes
        ax.set(ylim=self._y_lim)
        ax.invert_yaxis()

        # This looks after the shared x-axis and the primary y-axis
        super()._configure_ax(ax)

        # Now we set up the secondary y-axis
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

    def _render_plot_sets(self, ax, plot_sets: Dict[str, PlotSet]):
        """
        Completely subclass the data rendering logic of the superclass()
        In this case we're not directly plotting photometric data,
        instead we'll do SED analysis and then plot the resulting data.
        """
        delta_ts = self._param("delta_t", [1, 2, 3, 5, 10, 20])
        lambda_cs = self._param("lambda_c", {"I": 806, "R": 658, "V": 551, "B": 445, "UVM2": 224.6, "UVW2": 192.8})
        nu_cs = self._param("nu_c", {"I": 3.72e14, "R": 4.556e14, "V": 5.441e14, "B": 6.737e14, "UVM2": 1.335e15, "UVW2": 1.555e15})
        df = SpectralEvolutionDistributionPlot._perform_sed_analysis_magnitudes(plot_sets, lambda_cs, nu_cs, delta_ts)

        x_axis_frequency = (self._x_axis == self._default_x_axis)
        ix = 0
        for delta_t in sorted(delta_ts):
            # Plot the error bars of the points
            if x_axis_frequency:
                dt_df = df.query(f"delta_t == {delta_t}").sort_values(by="nu_c")
                self._plot_df_to_error_bars_on_ax(ax, dt_df, "nu_c", "mag", "mag_err", "k", fmt=",")
                self._plot_df_to_lines_on_ax(ax, dt_df, "nu_c", "mag", "k")
                x_pos_eol = dt_df.iloc[-1, 2] + 0.01

            else:
                dt_df = df.query(f"delta_t == {delta_t}").sort_values(by="lambda_c")
                self._plot_df_to_error_bars_on_ax(ax, dt_df, "lambda_c", "mag", "mag_err", "k", fmt=",")
                self._plot_df_to_lines_on_ax(ax, dt_df, "lambda_c", "mag", "k")
                x_pos_eol = dt_df.iloc[-1, 1] + 10

            y_pos = dt_df.iloc[-1, 5]
            # TODO: specific to this plot, handle a crush
            if ix == 5:
                y_pos += 0.2

            # Annotate the Delta t at the right end of each line
            label = f"$\\Delta t={delta_t:.2f}$" if delta_t != int(delta_t) else f"$\\Delta t={delta_t}$"
            ax.annotate(label, xycoords="data", xy=(x_pos_eol, y_pos))
            ix += 1

        # Now annotate the bands - along the top for now
        if x_axis_frequency:
            for band in nu_cs:
                ax.annotate(band, xycoords="data", xy=(np.log10(nu_cs[band]), 6.5), horizontalalignment="center")
        else:
            for band in lambda_cs:
                x_pos = lambda_cs[band] + (20 if band == "UVM2" else 0)
                ax.annotate(band, xycoords="data", xy=(x_pos, 6.5), horizontalalignment="center")
        return

    @classmethod
    def _perform_sed_analysis_magnitudes(cls, plot_sets: Dict[str, PlotSet],
                                         lambda_c_lookup: Dict, nu_c_lookup: Dict, delta_ts: Dict) -> DataFrame:
        rows = []
        for plot_set_key in plot_sets:
            plot_set = plot_sets[plot_set_key]
            band = plot_set.param("set")
            label = plot_set.label

            # Now use the fits to calculate magnitudes at the requested time intervals
            for delta_t in delta_ts:
                mag = plot_set.fits.find_y_value(delta_t)
                if mag is not None:
                    rows.append({"band": band, "lambda_c": lambda_c_lookup[band], "nu_c": np.log10(nu_c_lookup[band]),
                                 "label": label, "delta_t": delta_t, "mag": mag.nominal_value, "mag_err": mag.std_dev})

        if len(rows) > 0:
            df = DataFrame.from_records(rows, columns=rows[0].keys())
        else:
            df = None
        return df
