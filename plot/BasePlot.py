from abc import ABC, abstractmethod
from typing import Dict, Type
import matplotlib
import matplotlib.pyplot as plt


class BasePlot(ABC):
    """
    Base class for a configurable data plot
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
    def _x_size(self):
        return self._param("x_size", self._default_x_size) * self._PLOT_SCALE_UNIT

    @property
    def _y_size(self):
        return self._param("y_size", self._default_y_size) * self._PLOT_SCALE_UNIT

    @property
    def _show_title(self):
        return self._param("show_title", self._default_show_title)

    @property
    def _show_legend(self):
        return self._param("show_legend", self._default_show_legend)

    @property
    def _legend_loc(self):
        return self._param("legend_loc", self._default_legend_loc)

    @classmethod
    def create(cls, type_name: str, plot_param: Dict) -> Type["BasePlot"]:
        """
        Factory method for creating a BasePlot of the chosen type with the requested parameters dictionary.
        Will raise a KeyError if the type_name is not a recognised subclass.
        """
        ctor = cls._get_subclass_hierarchy()[type_name.casefold()]
        plot = ctor(plot_param)
        return plot

    def plot_to_file(self, plot_sets: Dict, file_name: str, title: str = None):
        """
        Convenience method to create, plot, save and close a MagnitudeLogTimeOnSingleAxisPlot
        """
        self._initialize_plot_for_file(title)

        fig = self._render_plot(plot_sets, title)
        if fig is not None:
            self._save_current_plot_to_file(file_name)
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to file.")
        return

    def plot_to_screen(self, plot_sets: Dict, title: str = None):
        """
        Convenience method to create, plot, save and close a MagnitudeLogTimeOnSingleAxisPlot
        """
        self._initialize_plot_for_screen(title)

        fig = self._render_plot(plot_sets, title)
        if fig is not None:
            self._show_current_plot_on_screen()
            plt.close(fig)
        else:
            self._log("No figure generated.  Nothing to write to display.")
        return

    @abstractmethod
    def _render_plot(self, bands: Dict, title: str) -> plt.figure:
        """
        Render the requested plot returning a matplotlib figure which can be displayed or printed as required.
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

