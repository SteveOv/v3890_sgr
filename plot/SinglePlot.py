from abc import ABC, abstractmethod
from typing import Dict, List
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
from plot import BasePlot, PlotData, PlotSet


class SinglePlot(BasePlot, ABC):
    """
    Produces a Rate vs Delta-time plot for 1 or more bands on a single axis, optionally overlaying with fitted slopes.
    The following plot params are supported (in addition to the standard params);
        show_data (True) - plot the raw data
        show_fits (False) - draw the line fits
        x_scale_log/y_scale_log - set the relevant axis to a log scale
        x_label/y_label - set the label of the relevant axis
        x_lim - set the limits of the x-axis
        x_ticks - the tick values/labels to display
        y_shift (0) - optional shift in the y-axis for each subsequent data_set
    For each rate the following rate_params are supported:
        color
        label
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_x_label = "x data"
        self._default_x_lim = (-1, 100)
        self._default_x_ticks = np.arange(10, 100, 10)

        self._default_y_label = "y data"
        self._default_y_shift = 0
        return

    def _render_plot(self, plot_data: PlotData, title: str) -> plt.figure:
        # Make it possible for subtype to override creating the figure and axis
        fig = self._create_fig()
        ax = self._create_ax(fig)

        if self._show_title and title is not None:
            ax.set_title(title)

        # Make it possible for subtype to override the config of the axis
        self._configure_ax(ax)

        # Hooks for the subtype to plot each data type
        self._render_plot_sets(ax, plot_data.plot_sets)

        # Hook for subtype to choose whether/how to render epoch data
        self._render_epochs(ax, plot_data.epochs)

        if self._show_legend:
            ax.legend(loc=self._legend_loc)
        return fig

    def _create_fig(self):
        return plt.figure(figsize=(self._x_size, self._y_size), constrained_layout=True)

    def _create_ax(self, fig):
        return fig.add_subplot(1, 1, 1)

    def _configure_ax(self, ax):
        ax.set_xlabel(self._param("x_label", self._default_x_label))
        ax.set_ylabel(self._param("y_label", self._default_y_label))

        ax.set_xticks(self._param("x_ticks", self._default_x_ticks), minor=False)
        ax.set(xlim=self._param("x_lim", self._default_x_lim))

        ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
        return

    def _render_plot_sets(self, ax, plot_sets: Dict[str, PlotSet]):
        ix = 0
        for set_key in plot_sets.keys():
            ps = plot_sets[set_key]
            self._render_plot_set(ax, ix, ps)
            ix += 1

    def _render_plot_set(self, ax, ix: int, ps: PlotSet):
        y_shift = self._param("y_shift", self._default_y_shift) * ix
        label = self._define_data_label(ps.label, y_shift)
        color = ps.color
        self._plot_points_to_error_bars_on_ax(ax,
                                              x_points=ps.x, y_points=ps.y, y_err_points=ps.y_err,
                                              color=color, label=label, y_shift=y_shift)
        return

    def _render_epochs(self, ax, epochs: Dict[str, float]):
        # TODO
        return

    def _define_data_label(self, label: str, shift_by: float = 0):
        return label + (F" (shifted {shift_by:+.1f})" if shift_by != 0 else "")

    # TODO: Maybe these would be better on the BasePlot
    def _plot_df_to_error_bars_on_ax(self, ax, df: DataFrame, x_col: str, y_col: str, y_err_col: str,
                                     color: str, label: str = None, y_shift: float = 0, fmt: str = ","):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        return self._plot_points_to_error_bars_on_ax(
            ax, df[x_col], df[y_col], df[y_err_col], color, label, y_shift, fmt)

    def _plot_points_to_error_bars_on_ax(self,
                                         ax, x_points: List[float], y_points: List[float], y_err_points: List[float],
                                         color: str, label: str = None, y_shift: float = 0, fmt: str = ","):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        # TODO: extend this to include x_err too
        return ax.errorbar(x_points, np.add(y_points, y_shift), yerr=y_err_points,
                           label=label, fmt=fmt, color=color, fillstyle='full', markersize=self._marker_size,
                           capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)

    def _plot_df_to_lines_on_ax(self, ax, df: DataFrame, x_col: str, y_col: str,
                                color: str, label: str = None, y_shift: float = 0, line_style: str = "-"):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        return self._plot_points_to_lines_on_ax(ax, df[x_col], df[y_col], color, label, y_shift, line_style)

    def _plot_points_to_lines_on_ax(self, ax, x_points: List[float], y_points: List[float],
                                    color: str, label: str = None, y_shift: float = 0, line_style: str = "-"):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        return ax.plot(x_points, np.add(y_points, y_shift), line_style,
                       label=label, color=color, linewidth=self._line_width, alpha=1, zorder=2)
