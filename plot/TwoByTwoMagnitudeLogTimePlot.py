from typing import Dict
import warnings
import matplotlib.pyplot as plt
from plot import SingleMagnitudeTimePlot, PlotData, PlotSet


class TwoByTwoMagnitudeLogTimePlot(SingleMagnitudeTimePlot):
    """
    Produces a Magnitude vs log(Delta-time) plot for 1 or more bands on a single axis,
    optionally overlaying data with fitted slopes and separately a second axis showing the residuals from the fit.
    """
    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_show_legend = False

        # Override the parent - as this plot is for fits it's "always" going to use a log x scale
        self._default_x_scale_log = True
        return

    def _render_plot(self, plot_data: PlotData, title: str = "Magnitude v $\\log($\\Delta t)$") -> plt.figure:
        """
        Produce a figure with up to 4 (2 x 2) Magnitude v log(time) plots, for each of the passed band data.
        """
        show_breaks = self._param("show_breaks", False)
        show_title = self._param("show_title", True)

        # TODO: look at creating the axes on the fly as this approach is hard coded to 4 axes always
        fig, axes = plt.subplots(2, 2, figsize=(self._x_size, self._y_size))
        if show_title and title is not None:
            fig.suptitle(title)

        ax_ix = 0
        for plot_set_key in plot_data.plot_sets.keys():
            ps = plot_data.plot_sets[plot_set_key]

            if ax_ix > 3:
                warnings.warn("More than four bands specified for this plot.  Only the first four will be shown")
                break

            # Get the super class to set up the ax - it knows how to configure it for linear or log x scale.
            ax = axes.flat[ax_ix]
            super()._configure_ax(ax)
            ax.set_ylabel(self._param("y_label", F"{ps.label} Apparent magnitude [mag]"))

            # Get the super class to render the data.
            # It knows how to render mags v days on linear or log x-scale and will optionally draw of the fits.
            self._render_plot_set(ax, 0, ps)

            # Plotting breaks are specific to this type of plot, so we do that here.
            if show_breaks and ps.has_param("breaks"):
                # Replace the minor x-axis ticks with the breaks specific to this plot set.
                # Labels ar the values to 2 dp, rotated 90deg and within the axis.
                ax.set_xticks(ps.param("breaks"), minor=True)
                ax.set_xticklabels(["%.2f" % x for x in ps.param("breaks""")], minor=True)
                ax.tick_params(which='minor', axis='x', direction='inout', pad=-25, labelsize='x-small',
                               labelcolor='gray', labelrotation=90)
                ax.grid(which='minor', linestyle='--', linewidth=self._line_width, alpha=0.3)

            ax_ix += 1

        plt.tight_layout(pad=2.8, h_pad=1.0, w_pad=1.0)
        return
