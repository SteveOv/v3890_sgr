from typing import List, Tuple
from uncertainties import UFloat
from matplotlib.axes import Axes
import numpy as np
from fitting.Fit import Fit


class InterpolatedFit(Fit):

    def __init__(self, id: int,
                 range_from: float = None, range_to: float = None,
                 prior_fit: Fit = None, next_fit: Fit = None):

        super().__init__(id, x_endpoints=[], y_endpoints=[],
                         range_from=range_from, range_to=range_to)

        self.prior_fit = prior_fit
        self.next_fit = next_fit

    def __str__(self) -> str:
        text = super().__str__()
        if self._prior_fit is not None:
            text += f" Interpolating from ({self._prior_fit._x_endpoints[-1]}, {self._prior_fit._y_endpoints[-1]})"
        if self._next_fit is not None:
            text += f" to ({self._next_fit._x_endpoints[1]}, {self._next_fit._y_endpoints[1]})."
        return text

    @property
    def prior_fit(self) -> Fit:
        return self._prior_fit

    @prior_fit.setter
    def prior_fit(self, value: Fit):
        self._prior_fit = value

    @property
    def next_fit(self) -> Fit:
        return self._next_fit

    @next_fit.setter
    def next_fit(self, value: Fit):
        self._next_fit = value

    @property
    def has_fit(self) -> bool:
        return self._next_fit is not None and self._prior_fit is not None

    def draw_on_ax(self, ax: Axes, color: str, line_style: str = "--", line_width: float = 1.0,
                   alpha: float = 0.5, z_order: float = 2.0, label: str = None, y_shift: float = 0,
                   annotate: bool = True, annotation_format: str = r"$\alpha_{%d}$"):
        # Overrides the default line_style to use
        return super().draw_on_ax(ax, color, line_style, line_width, alpha, z_order,
                                  label, y_shift, annotate, annotation_format)

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        return [], []

    def find_peak_y_value(self, is_minimum: bool) -> (float, UFloat):
        return None

    def find_x_value(self, y_value: UFloat) -> float:
        return None

    def find_y_value(self, x_value: float) -> UFloat:
        return None

    def _calculate_plot_points(self, ax: Axes, y_shift: float = 0.0):
        if self._prior_fit is not None and self._next_fit is not None:
            # The y-values may need to be interpreted
            # A more generic approach would be to use properties of the prior/next Fit to work out the linear
            # (x, y) values to interpolate a line between, but this works for now and is simple.
            y = [self._prior_fit._y_endpoints[-1], self._next_fit._y_endpoints[0]]
            if ax.get_yscale() == "log":
                y = np.power(10, y)

            # Range from/to are always in terms of public (linear) values so we use them for the x-values
            x = [self._prior_fit.range_to, self._next_fit.range_from]

            return x, y
        else:
            return
