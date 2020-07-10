from typing import Dict
import warnings
import matplotlib.pyplot as plt
from plot import BasePlot


class TwoByTwoMagnitudeLogTimePlot(BasePlot):
    """
    Produces a Magnitude vs log(Delta-time) plot for 1 or more bands on a single axis,
    optionally overlaying data with fitted slopes and separately a second axis showing the residuals from the fit.
    """
    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2
        return

    def _render_plot(self, plot_sets: Dict, title: str = "Magnitude v $\\log($\\Delta t)$") -> plt.figure:
        """
        Produce a figure with up to 4 (2 x 2) Magnitude v log(time) plots, for each of the passed band data.
        """
        show_data = self._param("show_data", True)
        show_fits = self._param("show_fits", False)
        show_breaks = self._param("show_breaks", False)
        show_title = self._param("show_title", True)

        fig, axes = plt.subplots(2, 2, figsize=(self._x_size, self._y_size))
        if show_title and title is not None:
            fig.suptitle(title)

        ax_ix = 0
        for plot_set_key in plot_sets.keys():
            plot_set = plot_sets[plot_set_key]
            set_params = plot_set['params']
            set_df = plot_set['df']
            set_fits = plot_set['fits']
            color = set_params['color']

            if ax_ix > 3:
                warnings.warn("More than four bands specified for this plot.  Only the first four will be shown")
                break

            ax = axes.flat[ax_ix]
            ax_ix += 1

            ax.set_ylabel(self._param("y_label", F"{set_params['set']}-band Apparent magnitude [mag]"))
            ax.set_ylim(self._param("y_lim", (5.8, 19)))
            ax.invert_yaxis()

            # Major x-grid/labels for the days - data is log(day) so labels need to state actual days
            ax.set_xlabel(self._param("x_label", "$\\Delta t$ [days]"))
            ax.set_xlim(self._param("x_lim", (-1.85, 2.05)))
            ax.set_xticks(self._param("x_ticks", (-1, 0, 1, 2)), minor=False)
            ax.set_xticklabels(self._param("x_tick_labels", ("0.1", "1", "10", "100", "1000", "10000")), minor=False)
            ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.5)

            # Minor x-grid/labels for the break points in the slopes - specific to each band.
            # The value of the breaks are of log(day) with equivalent labels, from params, in days.
            if show_breaks and "breaks" in set_params:
                ax.set_xticks(set_fits.breaks, minor=True)

                # Use the breaks as specified in the band config for the labels, as these are in terms of days (not log)
                ax.set_xticklabels(["%.2f" % x for x in set_params['breaks']], minor=True)
                ax.tick_params(which='minor', axis='x', direction='inout', pad=-25, labelsize='x-small',
                               labelcolor='gray', labelrotation=90)
                ax.grid(which='minor', linestyle='--', linewidth=self._line_width, alpha=0.3)

            if show_data:
                ax.errorbar(set_df['log_day'], set_df['mag'], yerr=set_df['mag_err'], label=set_params['label'],
                            fmt=",", color=color, fillstyle='full', markersize=self._marker_size, capsize=1,
                            ecolor=color, elinewidth=self._line_width, alpha=0.3, zorder=1)
            if show_fits:
                for fit in set_fits:
                    ax.plot(fit.x_points, fit.y_points,
                            self._param("fit_line_style", "-k"), linewidth=self._line_width, alpha=1, zorder=2)

        plt.tight_layout(pad=2.8, h_pad=1.0, w_pad=1.0)
        return fig
