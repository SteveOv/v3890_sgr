from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, List, Union
from pandas import DataFrame
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import itertools
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

    _subclasses = None

    def __init__(self, plot_params: Dict):
        self._log(F"Initializing, plot_params={plot_params}")
        self._params = plot_params

        # Used by the _draw/_plot methods
        self._default_line_width = 0.5
        self._default_alpha = 0.5
        self._default_marker_size = ((0.5 * 288) / self._DEFAULT_DPI) ** 2

        self._default_show_title = self._default_show_legend = True
        self._default_legend_loc = "upper right"

        self._default_x_size = self._default_y_size = 1

        self._default_x_label = "x data"
        self._default_x_lim = (-1, 100)
        self._default_x_ticks = np.arange(0, 110, 10)

        self._default_y_label = "y data"
        return

    @property
    def _print_dpi(self) -> float:
        return self._DEFAULT_DPI

    @property
    def line_width(self) -> float:
        return self._param("line_width", self._default_line_width)

    @property
    def alpha(self) -> float:
        return self._param("alpha", self._default_alpha)

    @property
    def marker_size(self) -> float:
        return self._param("marker_size", self._default_marker_size)

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

        if self.show_title and title is not None and ax is not None:
            ax.set_title(title, fontsize="medium")

        # Make it possible for subtype to override the config of the axis
        self._configure_ax(ax, **kwargs)

        # The hook for the specific subtype to plot its data to the Axes
        self._draw_plot_data(ax, **kwargs)

        if self.show_legend and ax is not None:
            ax.legend(loc=self.legend_loc, fontsize="medium")
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
        ax.grid(which='major', linestyle='-', linewidth=self.line_width * 0.75, alpha=self.alpha * 0.75)
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
                                     color: str, label: str = None, y_shift: float = 0, fmt: str = ",",
                                     line_width: float = None, alpha: float = None, z_order: float = 1):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        return self._plot_points_to_error_bars_on_ax(
            ax, df[x_col], df[y_col], df[y_err_col], color,
            label=label, y_shift=y_shift, fmt=fmt, line_width=line_width, alpha=alpha, z_order=z_order)

    def _plot_points_to_error_bars_on_ax(self,
                                         ax: Axes, x_points: List[float], y_points: List[float],
                                         y_err_points: List[float],
                                         color: str, label: str = None, y_shift: float = 0, fmt: str = ",",
                                         line_width: float = None, alpha: float = None, z_order: float = 1):
        """
        Plot the passed data as a sequence of error bars using standard formatting as configured for this instance.
        """
        if alpha is None:
            alpha = self.alpha
        if line_width is None:
            line_width = self.line_width
        # TODO: extend this to include x_err too
        return ax.errorbar(x_points, np.add(y_points, y_shift), yerr=y_err_points,
                           label=label, fmt=fmt, color=color, fillstyle='full', markersize=self.marker_size,
                           capsize=1, ecolor=color, elinewidth=line_width, alpha=alpha, zorder=z_order)

    def _plot_df_to_lines_on_ax(self, ax: Axes, df: DataFrame, x_col: str, y_col: str,
                                color: str, label: str = None, y_shift: float = 0, line_style: str = "-",
                                line_width: float = None, alpha: float = None, z_order: float = 2):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        return self._plot_points_to_lines_on_ax(ax, df[x_col], df[y_col], color, label=label, y_shift=y_shift,
                                                line_style=line_style, line_width=line_width, alpha=alpha, z_order=z_order)

    def _plot_points_to_lines_on_ax(self, ax: Axes, x_points: List[float], y_points: List[float],
                                    color: str, label: str = None, y_shift: float = 0, line_style: str = "-",
                                    line_width: float = None, alpha: float = None, z_order: float = 2):
        """
        Plot the passed data as a sequence of lines using standard formatting as configured for this instance.
        """
        if alpha is None:
            alpha = self.alpha
        if line_width is None:
            line_width = self.line_width
        return ax.plot(x_points, np.add(y_points, y_shift), line_style,
                       label=label, color=color, linewidth=line_width, alpha=alpha, zorder=z_order)

    def _draw_vertical_lines(self, ax: Axes, x, text: [Union[str, List[str]]] = None,
                             color: str = "k", line_width: float = None, line_style: str = ":",
                             h_align: str = "center", v_align: str = None, alpha: float = None,
                             text_top: bool = False, text_offset: float = 0.05, text_rotation: float = 90,
                             text_size: str = "xx-small"):
        """
        Will draw one or more vertical lines to the Axes from top to bottom at the required x positions (data coords).
        The optional text is written on the line at the required, proportional offset from the top/bottom (axes coords).
        """
        if alpha is None:
            alpha = self.alpha * 0.75
        if line_width is None:
            line_width = self.line_width * 0.75
        if v_align is None:
            v_align = "top" if text_top else "bottom"
        if isinstance(x, float):
            x = [x]
        if isinstance(text, str):
            text = [text]

        y_dummy = np.median(ax.get_ylim())
        for x_data_pos, this_text in itertools.zip_longest(x, text if text is not None else []):
            if x_data_pos is not None:
                # Translate the x data position into Axes position - we're only interested in the x coordinate.
                x_pos, _ = ax.transAxes.inverted().transform_point(ax.transData.transform_point((x_data_pos, y_dummy)))
                ax.vlines(x=x_pos, ymin=0, ymax=1, transform=ax.transAxes,
                          linestyles=line_style, linewidth=line_width, alpha=alpha, color=color)

                if this_text is not None:
                    y_pos = max(1 - text_offset, 0) if text_top else min(text_offset, 1)
                    ax.text(x_pos, y_pos, this_text, transform=ax.transAxes,
                            size=text_size, color=color, alpha=min([alpha * 2, 1]),
                            rotation=text_rotation, verticalalignment=v_align, horizontalalignment=h_align)

        return

    def _draw_horizontal_lines(self, ax: Axes, y, text: [Union[str, List[str]]] = None,
                               color: str = "k", line_width: float = None, line_style: str = ":",
                               h_align: str = None, v_align: str = "center", alpha: float = None,
                               text_right: bool = False, text_offset: float = 0.05, text_size: str = "x-small"):
        """
        Will draw one or more horizontal lines to the Axes from top to bottom at the required y positions.
        The optional text will be written on the line at the required, proportional offset from the left/right.
        """
        if alpha is None:
            alpha = self.alpha * 0.75
        if line_width is None:
            line_width = self.line_width * 0.75
        if h_align is None:
            h_align = "right" if text_right else "left"
        if isinstance(y, float):
            y = [y]
        if isinstance(text, str):
            text = [text]

        x_dummy = np.median(ax.get_xlim())
        for y_data_pos, this_text in itertools.zip_longest(y, text if text is not None else []):
            if y_data_pos is not None:
                # Translate the y data position into Axes position - we're only interested in the y coordinate.
                _, y_pos = ax.transAxes.inverted().transform_point(ax.transData.transform_point((x_dummy, y_data_pos)))
                ax.vlines(xmin=0, xmax=1, y=y_pos, transform=ax.transAxes,
                          linestyles=line_style, linewidth=line_width, alpha=alpha, color=color)

                if this_text is not None:
                    x_pos = max(1 - text_offset, 0) if text_right else min(text_offset, 1)
                    ax.text(x_pos, y_pos, this_text, transform=ax.transAxes,
                            size=text_size, color=color, alpha=min([alpha * 2, 1]),
                            verticalalignment=v_align, horizontalalignment=h_align)
        return
