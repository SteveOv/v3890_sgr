from abc import ABC, abstractmethod
from typing import List
import numpy as np
import uncertainties
import copy
from fitting import FitBase


class FitBase(ABC):
    """
    Base class for a fit to a range of data
    """

    def __init__(self, id: int, range_from: float, range_to: float,
                 x_endpoints: List[float], y_endpoints: List[uncertainties.UFloat]):
        self.__id = id
        self._range_from = range_from
        self._range_to = range_to

        self._x_endpoints = x_endpoints
        self._y_endpoints = y_endpoints

    def __str__(self):
        text = f"{type(self).__name__}[{self.id}] covering x in ({self.range_from}, {self.range_to})"
        return text

    @property
    def id(self) -> int:
        return self.__id

    @property
    def x_endpoints(self) -> List[float]:
        return self._x_endpoints

    @property
    def y_endpoints(self) -> List[uncertainties.UFloat]:
        return self._y_endpoints

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
    def copy(cls, src: FitBase, x_shift: float = 0, y_shift: float = 0, new_id: int = None) -> FitBase:
        """
        Make a copy of the source Fit, optionally applying a shift to the x and y values
        and assigning a new subscript to its symbol. Must be overridden if subclass extends FitBase.
        """
        if isinstance(src, FitBase):
            cp = cls(src.id if new_id is None else new_id,
                     np.add(src._range_from, x_shift), np.add(src._range_to, x_shift),
                     np.add(copy.copy(src._x_endpoints), x_shift), np.add(copy.copy(src._y_endpoints), y_shift))
        else:
            cp = None
        return cp

    @classmethod
    @abstractmethod
    def fit_to_data(
            cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float) \
            -> FitBase:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
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


