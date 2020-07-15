from abc import ABC, abstractmethod
from typing import List
import numpy as np
import uncertainties
import copy
from matplotlib.axes import Axes
from fitting import Fit


class Fit(ABC):
    """
    Base class for a fit to a range of data
    """

    def __init__(self, id: int, x_endpoints: List[float], y_endpoints: List[uncertainties.UFloat],
                 range_from: float = None, range_to: float = None):
        self.__id = id
        self._x_endpoints = x_endpoints
        self._y_endpoints = y_endpoints
        self._range_from = min(x_endpoints) if x_endpoints is not None and range_from is None else range_from
        self._range_to = max(x_endpoints) if x_endpoints is not None and range_to is None else range_to
        return

    def __str__(self):
        text = f"{type(self).__name__}[{self.id}] covering x in ({self.range_from}, {self.range_to})"
        return text

    @property
    def id(self) -> int:
        return self.__id

    @property
    def range_from(self) -> float:
        return self._range_from

    @property
    def range_to(self) -> float:
        return self._range_to

    @property
    @abstractmethod
    def has_fit(self) -> bool:
        """
        Indicates whether this Fit instance represents a valid Fit or is a null/non fit
        """
        pass

    @classmethod
    def copy(cls, src: Fit, x_shift: float = 0, y_shift: float = 0, new_id: int = None) -> Fit:
        """
        Make a copy of the source Fit, optionally applying a shift to the x and y values
        and assigning a new subscript to its symbol. Must be overridden if subclass extends Fit.
        """
        if isinstance(src, Fit):
            cp = cls(src.id if new_id is None else new_id,
                     np.add(copy.copy(src._x_endpoints), x_shift), np.add(copy.copy(src._y_endpoints), y_shift),
                     range_from=np.add(src._range_from, x_shift), range_to=np.add(src._range_to, x_shift))
        else:
            cp = None
        return cp

    @abstractmethod
    def draw_on_ax(self, ax: Axes, color: str, line_width: float = 0.5, label: str = None, y_shift: float = 0):
        """
        Gets the Fit to draw itself onto the passed matplotlib ax
        """
        pass

    @abstractmethod
    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        """
        Get the residuals derived from the passed list of data points (xi, yi) compared to the Fit
        Returns a tuple containing lists of xi values and accompanying dyi residual values
        """
        pass

    @abstractmethod
    def find_peak_y_value(self, is_minimum: bool) -> (float, uncertainties.UFloat):
        """
        Find the peak y value of this Fit.  Returns a tuple of the x value and y_value where found.
        """
        pass

    @abstractmethod
    def find_x_value(self, y_value: uncertainties.UFloat) -> float:
        """
        Returns the first x (dependent) value which matches the passed y value, based on the fit.
        """
        pass

    @abstractmethod
    def find_y_value(self, x_value: float) -> uncertainties.UFloat:
        """
        Returns the y (dependent) value from the passed x value, based on the fit.
        """
        pass

    def is_in_range(self, x_value) -> bool:
        """
        Returns whether the passed x_value is within the x range of this Fit
        """
        return (x_value >= min(self._x_endpoints)) & (x_value <= max(self._x_endpoints))


