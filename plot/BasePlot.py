from abc import ABC, abstractmethod
from typing import Dict, Type, List
from pandas import DataFrame
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from plot import PlotData


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
        return

    @property
    def _print_dpi(self):
        return self._DEFAULT_DPI

    @property
    def _screen_dpi(self):
        return self._DEFAULT_DPI

    @property
    def x_size(self):
        return self._param("x_size", self._default_x_size) * self._PLOT_SCALE_UNIT

    @property
    def y_size(self):
        return self._param("y_size", self._default_y_size) * self._PLOT_SCALE_UNIT

    @property
    def show_title(self):
        return self._param("show_title", self._default_show_title)

    @property
    def show_legend(self):
        return self._param("show_legend", self._default_show_legend)

    @property
    def legend_loc(self):
        return self._param("legend_loc", self._default_legend_loc)

    @classmethod
    def create(cls, type_name: str, plot_params: Dict) -> Type["BasePlot"]:
        """
        Factory method for creating a BasePlot of the chosen type with the requested parameters dictionary.
        Will raise a KeyError if the type_name is not a recognised subclass.
        """
        ctor = cls._get_subclass_hierarchy()[type_name.casefold()]
        plot = ctor(plot_params)
        return plot

    def plot_to_file(self, plot_data: PlotData, file_name: str, title: str = None):
        """
        Convenience method to create, plot, save and close a MagnitudeLogTimeOnSingleAxisPlot
        """
        self._initialize_plot_for_file(title)

        fig = self._draw_plot(plot_data, title)
        if fig is not None:
            self._save_current_plot_to_file(file_name)
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to file.")
        return

    def plot_to_screen(self, plot_data: PlotData, title: str = None):
        """
        Convenience method to create, plot, save and close a MagnitudeLogTimeOnSingleAxisPlot
        """
        self._initialize_plot_for_screen(title)

        fig = self._draw_plot(plot_data, title)
        if fig is not None:
            self._show_current_plot_on_screen()
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to display.")
        return

    @abstractmethod
    def _draw_plot(self, plot_data: PlotData, title: str) -> plt.figure:
        """
        Draw the requested plot returning a matplotlib figure which can be displayed or printed as required.
        """
        pass

    def _log(self, text):
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

    def _initialize_plot_for_file(self, title: str):
        self._log(F"Preparing '{title}' for printing to file.".replace("\n", ""))
        matplotlib.use("Agg")
        plt.ioff()
        plt.rc("font", size=8)
        return

    def _initialize_plot_for_screen(self, title: str, backend: str = "TkAgg"):
        print(F"Preparing '{title}' for printing to screen.".replace("\n", ""))
        matplotlib.use(backend)
        plt.rc("font", size=8)
        return

    def _save_current_plot_to_file(self, file_name: str):
        print(f"{self.__class__.__name__} sending current plot to file '{file_name}'.")
        plt.savefig(file_name, dpi=self._print_dpi)
        return

    def _show_current_plot_on_screen(self):
        print(f"{self.__class__.__name__} sending current plot to the screen.")
        plt.show(dpi=self._screen_dpi)
        return

    def _param(self, key: str, default=None):
        """
        Gets the value of the requested parameter, or return the default if not present.
        """
        value = default if key not in self._params else self._params[key]
        # self._log(f"_param[{key}] == '{value}' (default='{default}')")
        return value

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
