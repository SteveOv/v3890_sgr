from typing import List
from uncertainties import UFloat
from matplotlib.axes import Axes
from fitting import Fit


class NullFit(Fit):
    """
    A simple fit indicating that no data was fitted
    """

    def __init__(self, id: int, x_endpoints: List[float], y_endpoints: List[UFloat],
                 range_from: float = None, range_to: float = None):
        super().__init__(id, x_endpoints, y_endpoints, range_from=range_from, range_to=range_to)
        return

    def __str__(self):
        return F"{self.__class__.__name__}[{self.id}] covering x in ({self.range_from}, {self.range_to})"

    @property
    def has_fit(self) -> bool:
        return False

    def draw_on_ax(self, ax: Axes, color: str, line_width: float = 0.5, alpha: float = 1.0, z_order: float = 2.0,
                   label: str = None, y_shift: float = 0):
        # Nothing to draw
        return

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        # No residuals
        return [], []

    def find_peak_y_value(self, is_minimum: bool) -> (float, UFloat):
        # No values
        return None

    def find_x_value(self, y_value: UFloat) -> float:
        # No values
        return None

    def find_y_value(self, x_value: float) -> UFloat:
        # No values
        return None

