from typing import List, Dict
import copy
from plot.PlotSet import PlotSet


class PlotData:
    """
    The plot sets, epochs and config that can be passed to a Plot for plotting.
    """

    def __init__(self, plot_set_configs: List[Dict], light_curves: Dict, epochs: Dict[str, float] = {}):
        self.__plot_sets = {}
        self.__epochs = epochs

        # The plot_sets config dictionary contains on or more plot_set dictionaries which will have a data_sets item
        # giving the path to the source data/fits/params and zero or more params which overwrite the data_set params.
        for plot_set_config in plot_set_configs:
            # Decompose the the data_sets path.   Expected format <DataSource>/<LightCurve>/[data_keys]
            # (data keys may refer to bands or rate types), where <DataSource>/<LightCurve> is the light_curve key.
            # TODO: use a regex to parse the set key
            data_sets_path = plot_set_config['data_sets'].split("/")
            plot_lc_key = f"{data_sets_path[0]}/{data_sets_path[1]}"
            light_curve = light_curves[plot_lc_key]
            if len(data_sets_path) > 2:
                set_keys = data_sets_path[2].split(",")
            else:
                # All the sets within the light-curve
                set_keys = light_curve.keys()

            for set_key in set_keys:
                # Within the light_curve are one or more data_sets, and we use the keys to pick from those
                data_set = light_curve[set_key]

                # These will be each set data in the source light curve; each contains df and optional fits & params
                df = data_set["df"]
                fits = PlotData._read_param(data_set, "fits")
                params = copy.copy(PlotData._read_param(data_set, "params", {}))

                # Now we look to the plot set data which will contain any param overrides
                for override_key in plot_set_config:
                    if override_key != "data_sets":
                        params[override_key] = plot_set_config[override_key]

                # TODO: hard coded the relation between data sources and
                plot_set_key = F"{plot_lc_key}/{set_key}"
                plot_set = PlotSet(plot_set_key, df, params, fits)
                self.__plot_sets[plot_set_key] = plot_set
        return

    def __str__(self):
        return f"{self.__class__.__name__}[{self.__plot_sets.keys()}]"

    @property
    def plot_sets(self) -> Dict[str, PlotSet]:
        return self.__plot_sets

    @property
    def epochs(self) -> Dict[str, float]:
        return self.__epochs

    @classmethod
    def _read_param(cls, params: Dict, key: str, default=None):
        return params[key] if key in params else default

