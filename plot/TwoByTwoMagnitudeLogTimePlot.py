import warnings
from plot.PlotData import *
from plot.MagnitudeTimePlot import *


class TwoByTwoMagnitudeLogTimePlot(MagnitudeTimePlot):
    """
    Produces a Magnitude vs log(Delta-time) plot for 1 or more bands on a single axis,
    optionally overlaying data with fitted slopes and separately a second axis showing the residuals from the fit.
    """
    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)
        self._default_x_size = 2
        self._default_y_size = 2
        self._default_show_legend = False

        self._default_show_breaks = False

        # Override the parent - as this plot is for fits it's "always" going to use a log x scale
        self._default_x_scale_log = True
        return

    @property
    def show_breaks(self) -> bool:
        return self._param("show_breaks", self._default_show_breaks)

    @property
    def show_epochs(self) -> bool:
        # The breaks are presented as epochs on each set of axes.  Override any default behaviour.
        return self.show_breaks

    @property
    def show_epoch_labels(self) -> bool:
        return self.show_breaks

    @property
    def y_shift(self) -> float:
        # Never allow a y_shift to be set
        return 0

    def _draw_plot(self, plot_data: PlotData, title: str = "Magnitude v $\\log($\\Delta t)$") -> Figure:
        """
        Produce a figure with up to 4 (2 x 2) Magnitude v log(time) plots, for each of the passed band data.
        """
        # TODO: look at creating the axes on the fly as this approach is hard coded to 4 axes always
        fig, axes = plt.subplots(2, 2, figsize=(self.x_size, self.y_size))
        if self.show_title and title is not None:
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
            # It knows how to render mags v days on linear or log x-scale and will optionally draw the fits if required.
            self._draw_plot_set(ax, 0, ps)

            # Plotting breaks are specific to this type of plot so we do that here by subverting epoch drawing.
            if self.show_breaks and ps.has_param("breaks"):
                epochs_from_breaks = dict(zip(["%.2f" % x for x in ps.param("breaks")], ps.param("breaks")))
                self._draw_epochs(ax, epochs_from_breaks)

            ax_ix += 1

        plt.tight_layout(pad=2.8, h_pad=1.0, w_pad=1.0)
        return fig
