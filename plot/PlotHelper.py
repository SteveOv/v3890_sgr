from typing import Dict
import copy
from plot import BasePlot


class PlotHelper:
    """
    Helper for invoking plots from configuration settings.
    """

    @classmethod
    def plot_to_file(cls, plot_config: Dict, light_curves: Dict):
        print()
        plot_title = plot_config['title']
        if cls._is_plot_enabled(plot_config):
            # The params specify the overall look/feel of the plot
            plot_params = plot_config["params"]
            plot = BasePlot.create(plot_config['type'], plot_params)

            # The plot_sets contain the data and metadata for each set of data to plot
            plot_sets = cls._get_plot_sets(plot_config, light_curves)
            plot.plot_to_file(plot_sets=plot_sets, file_name=plot_config['file_name'], title=plot_title)
        else:
            print(F"{plot_config['type']} entitled '{plot_title}' is disabled. Skipping.")
        return

    @classmethod
    def plot_to_screen(cls, plot_config: Dict, light_curves: Dict):
        print()
        plot_title = plot_config['title']
        if cls._is_plot_enabled(plot_config):
            # The params specify the overall look/feel of the plot
            plot_params = plot_config["params"]
            plot = BasePlot.create(plot_config['type'], plot_params)

            # The plot_sets contain the data and metadata for each set of data to plot
            plot_sets = cls._get_plot_sets(plot_config, light_curves)
            plot.plot_to_screen(plot_sets=plot_sets, title=plot_title)
        else:
            print(F"{plot_config['type']} entitled '{plot_title}' is disabled. Skipping.")
        return

    @classmethod
    def _get_plot_sets(cls, plot_config: Dict, light_curves: Dict) -> Dict:
        """
        Sets up the plot_sets, which contain the data/params for each set of data to be included in a plot (bands/rates)
        The params associated with each plot_set are those copies over from the fitting/data source with
        overrides from the bands in the plot config

        Each plot_set contains the following
            "df": the DataFrame containing the source data
            "fits": the fitted light curve (0 or more fit instances)
            "params": conflation of the configuration light-curve/band params and the plot_set/params
                     (plot params override/extend these as necessary)
        """
        plot_sets = {}

        for plot_set_params in plot_config["plot_sets"]:
            # Decompose the the band key into the light_curve key and an optional list of bands
            # Expected format <DataSource>/<LightCurve>/[data_keys]  (data keys may refer to bands or rate types)
            # Where <DataSource>/<LightCurve> is the light_curve key
            parts = plot_set_params['data_sets'].split("/")
            plot_lc_key = f"{parts[0]}/{parts[1]}"
            plot_data_set_key = "" if len(parts) <= 2 else parts[2]

            light_curve = copy.deepcopy(light_curves[plot_lc_key])

            for lc_data_set_key in light_curve.keys():
                if len(plot_data_set_key) == 0 or lc_data_set_key in plot_data_set_key:
                    # Each plot_set has a key of the form {data_source}/{light_curve}/{data_key}
                    plot_set_key = f"{plot_lc_key}/{lc_data_set_key}"

                    # This is a set that is of interest.  Copy it over and apply any plot specific parameter overrides
                    plot_sets[plot_set_key] = light_curve[lc_data_set_key]
                    for override_key in plot_set_params.keys():
                        if override_key != "data_sets":
                            plot_sets[plot_set_key]["params"][override_key] = plot_set_params[override_key]
        return plot_sets

    @classmethod
    def _is_plot_enabled(cls, plot_config):
        return plot_config['enabled'] if 'enabled' in plot_config else True
