from abc import ABC
from typing import Dict
import numpy as np
import matplotlib.pyplot as plt
from fitting import StraightLineLogXFit
from plot import BasePlot, PlotData, PlotSet


class SinglePlot(BasePlot, ABC):
    """
    Produces a data vs Delta-time plot for 1+ PlotSets on a single axis, optionally overlaying with fitted lines.
    The following plot params are supported (in addition to the standard params defined by BasePlot);
        * show_data (True) - plot the raw data
        * show_fits (False) - draw the line fits
        * x_label/y_label - set the label of the relevant axis
        * x_lim - set the limits of the x-axis
        * x_ticks - the tick values/labels to display
        * y_shift (0) - optional shift in the y-axis for each subsequent data_set
    For each PlotSet the following rate_params are supported:
        * color
        * label
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_show_data = True
        self._default_show_fits = False

        self._default_x_label = "x data"
        self._default_x_lim = (-1, 100)
        self._default_x_ticks = np.arange(10, 100, 10)

        self._default_y_label = "y data"
        self._default_y_shift = 0
        return

    @property
    def show_data(self):
        return self._param("show_data", self._default_show_data)

    @property
    def show_fits(self):
        return self._param("show_fits", self._default_show_fits)

    @property
    def x_label(self):
        return self._param("x_label", self._default_x_label)

    @property
    def x_lim(self):
        return self._param("x_lim", self._default_x_lim)

    @property
    def x_ticks(self):
        return self._param("x_ticks", self._default_x_ticks)

    @property
    def y_label(self):
        return self._param("y_label", self._default_y_label)

    @property
    def y_shift(self):
        return self._param("y_shift", self._default_y_shift)

    def _draw_plot(self, plot_data: PlotData, title: str) -> plt.figure:
        """
        Override of the abstract _draw_plot() on BasePlot. The main routine for drawing the plot as a whole. Invokes the
        hooks for creating figure, ax and drawing to it.  Where possible, avoid overriding this, instead override
        the hooks/methods it calls (below).
        """
        # Make it possible for subtype to override creating the figure and axis
        fig = self._create_fig()
        ax = self._create_ax(fig)

        if self.show_title and title is not None:
            ax.set_title(title)

        # Make it possible for subtype to override the config of the axis
        self._configure_ax(ax)

        # Hooks for the subtype to plot each data type
        self._draw_plot_sets(ax, plot_data.plot_sets)

        # Hook for subtype to choose whether/how to render epoch data
        self._draw_epochs(ax, plot_data.epochs)

        if self.show_legend:
            ax.legend(loc=self.legend_loc)
        return fig

    def _create_fig(self):
        return plt.figure(figsize=(self.x_size, self.y_size), constrained_layout=True)

    def _create_ax(self, fig):
        return fig.add_subplot(1, 1, 1)

    def _configure_ax(self, ax):
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_xticks(self.x_ticks, minor=False)
        ax.set(xlim=self.x_lim)

        ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
        return

    def _draw_plot_sets(self, ax, plot_sets: Dict[str, PlotSet]):
        ix = 0
        for set_key in plot_sets.keys():
            ps = plot_sets[set_key]
            self._draw_plot_set(ax, ix, ps)
            ix += 1

    def _draw_plot_set(self, ax, ix: int, ps: PlotSet):
        this_y_shift = self.y_shift * ix
        label = self._define_data_label(ps.label, this_y_shift)
        color = ps.color

        # Render the base data
        if self.show_data:
            self._plot_points_to_error_bars_on_ax(ax, x_points=ps.x, y_points=ps.y, y_err_points=ps.y_err,
                                                  color=color, label=label, y_shift=this_y_shift)

        # Optionally draw any fitted lines
        if self.show_fits and ps.fits is not None:
            for fit in ps.fits:
                y_endpoints = fit.y_endpoints
                if isinstance(fit, StraightLineLogXFit):
                    x_endpoints = fit.linear_x_endpoints
                else:
                    x_endpoints = fit.x_endpoints

                fit_line, = self._plot_points_to_lines_on_ax(ax, x_endpoints, y_endpoints, color, y_shift=this_y_shift)

                # If we didn't show the corresponding data then attach the label to the fits
                if not self.show_data and fit_line is not None and len(label) > 0:
                    fit_line.set_label(label)
                    label = ""  # Stop the label being repeated for each subsequent fit in this plot_set's fits
        return

    def _draw_epochs(self, ax, epochs: Dict[str, float]):
        # TODO
        return

    def _define_data_label(self, label: str, shift_by: float = 0):
        return label + (F" (shifted {shift_by:+.1f})" if shift_by != 0 else "")
