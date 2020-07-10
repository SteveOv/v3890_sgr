from typing import Dict
from plot import SinglePlotSupportingLogAxes


class SingleRateTimePlot(SinglePlotSupportingLogAxes):
    """
    Produces a Rate vs Delta-time plot for 1 or more bands on a single axis.  Both axes support log scaling.

    TODO: support for fitted slopes
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params, x_axis_supports_log=True, y_axis_supports_log=True)

        self._default_x_label = "$\\Delta t$ [days]"
        self._default_y_label = "Count Rate (0.1 - 10 keV) [s$^{-1}$]"

        self._x_data_column = "day"
        self._y_data_column = "rate"
        self._y_err_column = "rate_err"
        return

