from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, List, Union
from pandas import DataFrame
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class BasePlot(ABC):
    """
    Abstract base class for a configurable data plot.  All plots are derived from this.
    Defines the basic public interface for all plots; @classmethod create() factory method
    and the plot_to_file()/plot_to_screen() instance methods.
    Also provides protected _param() method for reading from the plot_params dictionary with fallback on default value.

    Defines the following plot params
        * x_size, y_size (1, 1) - the size of the plot in _PLOT_SCALE_UNITS
        * show_title (True)
        * show_legend (True)
        * legend_loc ("upper right")
        * x_label/y_label - set the label of the relevant axis
        * x_lim - set the limits of the x-axis
        * x_ticks - the tick values/labels to display
    """
    _DEFAULT_DPI = 300
    _PLOT_SCALE_UNIT = 3.2
    _TITLE_SCALE_UNIT = 46

    _line_width = 0.5
    _marker_size = ((0.5 * 288) / _DEFAULT_DPI) ** 2

    _subclasses = None

    def __init__(self, plot_params: Dict):
        self._log(F"Initializing, plot_params={plot_params}")
        self._params = plot_params

        self._default_show_title = self._default_show_legend = True
        self._default_legend_loc = "upper right"

        self._default_x_size = self._default_y_size = 1

        self._default_x_label = "x data"
        self._default_x_lim = (-1, 100)
        self._default_x_ticks = np.arange(10, 100, 10)

        self._default_y_label = "y data"
        return

    @property
    def _print_dpi(self) -> float:
        return self._DEFAULT_DPI

    @property
    def x_size(self) -> float:
        return self._param("x_size", self._default_x_size) * self._PLOT_SCALE_UNIT

    @property
    def y_size(self) -> float:
        return self._param("y_size", self._default_y_size) * self._PLOT_SCALE_UNIT

    @property
    def show_title(self) -> bool:
        return self._param("show_title", self._default_show_title)

    @property
    def show_legend(self) -> bool:
        return self._param("show_legend", self._default_show_legend)

    @property
    def legend_loc(self) -> str:
        return self._param("legend_loc", self._default_legend_loc)

    @property
    def x_label(self) -> str:
        return self._param("x_label", self._default_x_label)

    @property
    def x_lim(self) -> List[float]:
        return self._param("x_lim", self._default_x_lim)

    @property
    def x_ticks(self) -> List[float]:
        return self._param("x_ticks", self._default_x_ticks)

    @property
    def x_tick_labels(self) -> List[str]:
        return self._param("x_tick_labels", self.x_ticks)

    @property
    def y_label(self) -> str:
        return self._param("y_label", self._default_y_label)

    @classmethod
    def create(cls, type_name: str, plot_params: Dict) -> Type["BasePlot"]:
        """
        Factory method for creating a BasePlot of the chosen type with the requested parameters dictionary.
        Will raise a KeyError if the type_name is not a recognised subclass.
        """
        ctor = cls._get_subclass_hierarchy()[type_name.casefold()]
        plot = ctor(plot_params)
        return plot

    def plot_to_file(self, file_name: Union[str, Path], title: str, **kwargs):
        """
        Convenience method to create, plot, save and close a plot based on this type.
        """
        self._log(F"Preparing '{title}' for printing to file.".replace("\n", ""))
        matplotlib.use("Agg")
        plt.ioff()
        plt.rc("font", size=8)

        fig = self._draw_plot(title, **kwargs)
        if fig is not None:
            self._log(f"Saving current plot to file '{file_name}'.")

            # Make sure the folder exists for the output.
            if not isinstance(file_name, Path):
                file_name = Path(file_name)
                if not file_name.parent.exists():
                    file_name.parent.mkdir(parents=True, exist_ok=True)

            plt.savefig(file_name, dpi=self._print_dpi)
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to file.")
        return

    def plot_to_screen(self, title: str, **kwargs):
        """
        Convenience method to create, plot, show to screen and close a plot based on this type.
        """
        print(F"Preparing '{title}' for printing to screen.".replace("\n", ""))
        matplotlib.use("TkAgg")
        plt.rc("font", size=8)

        fig = self._draw_plot(title, **kwargs)
        if fig is not None:
            self._log("Sending current plot to the screen.")
            plt.show()
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to display.")
        return

    def _draw_plot(self, title: str, **kwargs) -> Figure:
        """
        The main routine for drawing the plot as a whole.  Invokes the hooks for creating figure, ax and drawing to it.
        Where possible, avoid overriding this, instead override the hooks/methods it calls (below).
        """
        # Make it possible for subtype to override creating the figure and axis
        fig = self._create_fig()
        ax = self._create_ax(fig)

        if self.show_title and title is not None:
            ax.set_title(title)

        # Make it possible for subtype to override the config of the axis
        self._configure_ax(ax, **kwargs)

        # The hook for the specific subtype to plot its data to the Axes
        self._draw_plot_data(ax, **kwargs)

        if self.show_legend:
            ax.legend(loc=self.legend_loc)
        return fig

    def _create_fig(self) -> Figure:
        """
        Create the figure onto which the Axes and plot are to be drawn
        """
        return plt.figure(figsize=(self.x_size, self.y_size), constrained_layout=True)

    def _create_ax(self, fig: plt.figure):
        """
        Create the Axes onto which the plotted data will be drawn.
        """
        return fig.add_subplot(1, 1, 1)

    def _configure_ax(self, ax: Axes, **kwargs):
        """
        Configure the Axes onto which the plotted data will be drawn.
        """
        ax.set(xlim=self.x_lim, xlabel=self.x_label, ylabel=self.y_label)
        ax.set_xticks(self.x_ticks, minor=False)
        ax.set_xticklabels(self.x_tick_labels, minor=False)
        ax.grid(which='major', linestyle='-', linewidth=self._line_width, alpha=0.3)
        return

    @abstractmethod
    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        The method, to be overridden by subclasses, for plotting their data to the passes Axes
        """
        pass

    def _log(self, text):
        """
        Log some text to the console.
        """
        print(f"{self.__class__.__name__}: " + text)
        return

    @classmethod
    def _get_subclass_hierarchy(cls):
        """
        Gets all the subclasses descending the class hierarchy.
        Use instead of __subclasses__() which appears to only get immediate subclasses.
        """
        if cls._subclasses is None:
            cls._subclasses = cls._get_subclasses()
        return cls._subclasses

    @classmethod
    def _get_subclasses(cls):
        sc_dict = {}
        subclasses = cls.__subclasses__()
        for subclass in subclasses:
            sc_dict[subclass.__name__.casefold()] = subclass
            if issubclass(subclass, BasePlot):
                sc_dict.update(subclass._get_subclasses())
        return sc_dict

    def _param(self, key: str, default=None):
        """
        Gets the value of the requested parameter, or return the default if not present.
        """
        value = default if key not in self._params else self._params[key]
        # self._log(f"_param[{key}] == '{value}' (default='{default}')")
        return value

    def _plot_df_to_error_bars_on_ax(self, ax: Axes, df: DataFrame, x_col: str, y_col: str, y_err_col: str,
                                     color: str, label: str = None, y_shift: float = 0, fmt: str = ","):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        return self._plot_points_to_error_bars_on_ax(
            ax, df[x_col], df[y_col], df[y_err_col], color, label, y_shift, fmt)

    def _plot_points_to_error_bars_on_ax(self,
                                         ax: Axes, x_points: List[float], y_points: List[float], y_err_points: List[float],
                                         color: str, label: str = None, y_shift: float = 0, fmt: str = ","):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        # TODO: extend this to include x_err too
        return ax.errorbar(x_points, np.add(y_points, y_shift), yerr=y_err_points,
                           label=label, fmt=fmt, color=color, fillstyle='full', markersize=self._marker_size,
                           capsize=1, ecolor=color, elinewidth=self._line_width, alpha=0.5, zorder=1)

    def _plot_df_to_lines_on_ax(self, ax: Axes, df: DataFrame, x_col: str, y_col: str,
                                color: str, label: str = None, y_shift: float = 0, line_style: str = "-"):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        return self._plot_points_to_lines_on_ax(ax, df[x_col], df[y_col], color, label, y_shift, line_style)

    def _plot_points_to_lines_on_ax(self, ax: Axes, x_points: List[float], y_points: List[float],
                                    color: str, label: str = None, y_shift: float = 0, line_style: str = "-"):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        return ax.plot(x_points, np.add(y_points, y_shift), line_style,
                       label=label, color=color, linewidth=self._line_width, alpha=1, zorder=2)

    def _draw_vertical_lines(self, ax: Axes, x, text=None,
                             color="k", line_width=0.5, line_style=":", v_align=None, alpha=0.3,
                             text_top=True, text_offset=0.05, text_rotation=90, text_size="xx-small"):
        """
        Will draw one or more vertical lines to the Axes from top to bottom at the required x positions.
        The optional text will be written on the line at the required, proportional offset from the top/bottom.
        """
        y_lim = ax.get_ylim()
        y_inverted = ax.yaxis_inverted()
        y_min = min(y_lim)
        y_max = max(y_lim)

        # Plot a vertical line for each entry
        ax.vlines(x=x, ymin=y_min, ymax=y_max, linestyle=line_style, linewidth=line_width, alpha=alpha, color=color)

        # Add the optional text
        if text is not None and len(text):
            # Set the text position. Anchor to top/bottom with any offset a fraction of the scale towards the middle
            h_align = "center"
            y_scale = y_max - y_min

            # If the y axis is inverted just invert the text location and offset calculations to compensate.
            y_pos = y_max if text_top else y_min

            # Stop the offset from taking the text off the body of the plot
            y_offset = abs(y_scale * text_offset) if abs(text_offset) <= 0.90 else y_scale * 0.90

            # Align and position the text.
            if text_top:
                y_pos -= y_offset
                if v_align is None:
                    v_align = "top" if not y_inverted else "bottom"
            else:
                y_pos += y_offset
                if v_align is None:
                    v_align = "bottom" if not y_inverted else "top"

            for x_pos, this_text in zip(x, text):
                ax.text(x_pos, y_pos, this_text, size=text_size, color=color, alpha=min([alpha * 2, 1]),
                        rotation=text_rotation, verticalalignment=v_align, horizontalalignment=h_align)
        return
