from typing import Dict
from plot import BasePlot
from plot.PlotData import PlotData


class PlotHelper:
    """
    Helper for invoking plots from configuration settings.
    """

    @classmethod
    def create_plot_data_from_config(cls, plot_config: Dict, light_curves: Dict) -> PlotData:
        plot_set_configs = cls._read_param(plot_config, "plot_sets")
        plot_epochs = cls._read_param(plot_config, "epochs", {})
        return PlotData(plot_set_configs, light_curves, plot_epochs)

    @classmethod
    def plot_to_file(cls, plot_config: Dict, plot_data: PlotData):
        print()
        plot_title = cls._read_param(plot_config, "title", "")
        if cls._read_param(plot_config, "enabled", True):

            # The params specify the overall look/feel of the plot
            plot_params = plot_config["params"]
            plot = BasePlot.create(plot_config['type'], plot_params)

            # Now we get it to plot supplying the specific data to be plotted
            plot.plot_to_file(plot_data=plot_data, file_name=plot_config['file_name'], title=plot_title)
        else:
            print(F"{plot_config['type']} entitled '{plot_title}' is disabled. Skipping.")
        return

    @classmethod
    def plot_to_screen(cls, plot_config: Dict, plot_data: PlotData):
        print()
        plot_title = cls._read_param(plot_config, "title", "")
        if cls._read_param(plot_config, "enabled", True):

            # The params specify the overall look/feel of the plot
            plot_params = plot_config["params"]
            plot = BasePlot.create(plot_config['type'], plot_params)

            # Now we get it to plot supplying the specific data to be plotted
            plot.plot_to_screen(plot_data=plot_data, title=plot_title)
        else:
            print(F"{plot_config['type']} entitled '{plot_title}' is disabled. Skipping.")
        return

    @classmethod
    def _read_param(cls, params: Dict[str, any], key: str, default=None):
        return params[key] if key in params else default


