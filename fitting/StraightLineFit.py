from abc import ABC
from typing import List, Union, Tuple
import numpy as np
import uncertainties
from uncertainties import ufloat
from scipy.optimize import curve_fit
from matplotlib.axes import Axes
from fitting import Fit, FittedFit, StraightLineFit


class StraightLineFit(FittedFit, ABC):
    """
    A straight line, linear least squares fit to a range of data.
    Currently this is abstract as we are only using subclasses.
    """

    def __init__(self, id: int, x_endpoints: List[float], y_endpoints: List[uncertainties.UFloat],
                 range_from: float = None, range_to: float = None,
                 fit_params: (uncertainties.UFloat, uncertainties.UFloat) = None):
        super().__init__(id, x_endpoints, y_endpoints, range_from=range_from, range_to=range_to)
        self._fit_params = fit_params

    def __str__(self):
        if self.has_fit:
            text = f"{super().__str__()}: y = ({self.slope:.6fP} * x) + {self.const:.6fP}"
        else:
            text = f"{super().__str__()}: <No slope: insufficient data to fit line>"
        return text

    @property
    def slope(self) -> uncertainties.UFloat:
        """
        The slope of the straight line Fit.
        """
        return self._fit_params[0] if self._fit_params is not None else None

    @property
    def const(self) -> uncertainties.UFloat:
        """
        The constant of the straight line Fit - the y_value when x_value == 0.
        """
        return self._fit_params[1] if self._fit_params is not None else None

    @property
    def has_fit(self) -> bool:
        """
        Indicates whether this Fit instance represents a valid Fit or is a null/non fit
        """
        return self._fit_params is not None

    @classmethod
    def copy(cls, src: Fit, x_shift: float = 0, y_shift: float = 0, new_id: int = None) \
            -> Fit:
        """
        Makes a safe copy of this Fit instance (so the data really is a copy, not a reference)
        while optionally applying x/y shifts and a new id.
        """
        cp = super().copy(src, x_shift, y_shift, new_id)
        if isinstance(src, StraightLineFit) and src.has_fit:
            # Any shifts to the copied fit/line parameters don't change the slope, but will affect the const/y-intersect
            slope = src.slope

            # A y_shift is a simple shift up/down in the y-intersect corresponding to the change
            const = np.add(src.const, y_shift)

            # Shift in the X-direction will effectively move the y-intersect left/right by the x_shift value.
            # This means shifting the fit to the right by +1 will move the y-intersect by 1 to the left,
            # giving it the value the fitted line would previously have held at x = -1
            const = cls._y_from_straight_line_func(-x_shift, slope, const)
            cp._fit_params = (slope, const)
        return cp

    @classmethod
    def fit_to_data(cls, id: int, xi: List[float], yi: List[float],
                    dxi: List[float] = None, dyi: List[float] = None,
                    range_from: float = None, range_to: float = None) -> Fit:
        """
        Factory method to create a straight line Fit based on the passed data (xi, yi and delta yi)
        over the requested range of xi.  If dyi is none an unweighted fit will be made.  dxi values not supported.
        """
        fit = cls(id, [], [], range_from=range_from, range_to=range_to, fit_params=None)
        if xi is not None and yi is not None:
            lxi = len(xi)
            lyi = len(yi)
            if (0 < lxi == lyi) and (dyi is None or len(dyi) == lyi):
                # When absolute_sigma=True the values passed to sigma are treated as absolute value of same units as yi
                # and the variance of the popt params are in the diagonal of the returned pcov matrix. The sigmas of the
                # fitting params are the sqrt() of these values. When absolute_sigma=False the sigma values are used as
                # weighting, so I found best results using np.divide(1, dyi) for it (still inferior to absolute values).
                popt, pcov = curve_fit(cls._y_from_straight_line_func,
                                       xi, yi, sigma=dyi, absolute_sigma=True, check_finite=True)

                sigma = np.sqrt(np.diag(pcov))
                fit_params = (ufloat(popt[0], sigma[0]), ufloat(popt[1], sigma[1]))

                # If the from/to endpoints haven't been specified take the range from the extent of the xi data
                if range_from is None:
                    range_from = min(xi)
                if range_to is None:
                    range_to = max(xi)

                # Generate the plot points and residuals for the slope.
                # Ensure it extends over the limits of the range, not just the available data.
                # Don't use ufloats for the x/y_fit as we've no uncertainty for them and the will be used for plotting
                # the slopes.  Uncertainties in the slopes are encapsulated in the slope and const values.
                x_endpoints = [range_from, range_to]
                y_endpoints = cls._y_from_straight_line_func(x_endpoints, *popt)

                fit = cls(id, x_endpoints, y_endpoints, range_from=range_from, range_to=range_to, fit_params=fit_params)
        return fit

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        """
        Calculate the residuals - the y-difference between the y data points' nominal value
        and the slope as defined by this instance's slope and const
        """
        res_xi = []
        res_yi = []
        if xi is not None and yi is not None and len(xi) == len(yi) > 0:
            if self.has_fit:
                # Get the subset of the data which is within this fit's range
                in_range = self.is_in_range(xi)
                res_xi = np.array(xi)[in_range]
                temp_yi = np.array(yi)[in_range]

                # Just use the nominal values of the slope for residuals.
                s_nom = self.slope.nominal_value
                c_nom = self.const.nominal_value
                res_yi = np.subtract(temp_yi, self.__class__._y_from_straight_line_func(res_xi, s_nom, c_nom)).tolist()
        else:
            raise IndexError("The xi and yi Lists are not the same length")
        return res_xi, res_yi

    def find_peak_y_value(self, is_minimum: bool = False) -> (float, uncertainties.UFloat):
        """
        Find the peak y value of this Fit.  Returns a tuple of the x value and y_value where found.
        The is_minimum argument may be set to true, in which case the peak is considered the minimum y_value (not max)
        """
        peak_y = None
        at_x = None
        if self.has_fit:
            for x in self._x_endpoints:
                y_val = StraightLineFit._y_from_straight_line_func(x, self.slope, self.const)
                if peak_y is None or ((is_minimum and y_val < peak_y) | (is_minimum is False and y_val > peak_y)):
                    peak_y = y_val
                    at_x = x
        return at_x, peak_y

    def find_x_value(self, y_value: uncertainties.UFloat) -> float:
        """
        Finds the value of the independent (x) variable at the requested dependent (y) variable
        based on the nominal value of the the dependent variable.
        """
        if self.has_fit:
            # Publish fit details with uncertainties but we use the nominal values for finding a match
            x_val = StraightLineFit._x_from_straight_line_func(
                y_value.nominal_value, self.slope.nominal_value, self.const.nominal_value)
            if not self.is_in_range(x_val):
                x_val = None
        else:
            x_val = None
        return x_val

    def find_y_value(self, x_value: float) -> uncertainties.UFloat:
        """
        Finds the value of the dependent (y) variable at the requested independent (x) variable
        """
        if self.has_fit and self.is_in_range(x_value):
            y_val = StraightLineFit._y_from_straight_line_func(x_value, self.slope, self.const)
        else:
            y_val = None

        return y_val

    @classmethod
    def _y_from_straight_line_func(cls,
                                   x: Union[float, uncertainties.UFloat, List[float], List[uncertainties.UFloat]],
                                   m: Union[float, uncertainties.UFloat],
                                   c: Union[float, uncertainties.UFloat]) \
            -> Union[float, uncertainties.UFloat, List[float], List[uncertainties.UFloat]]:
        """
        Simple implementation of a straight line function: y = f(x, m, c) = mx + c
        """
        return np.add(np.multiply(m, x), c)

    @classmethod
    def _x_from_straight_line_func(cls,
                                   y: Union[float, uncertainties.UFloat, List[float], List[uncertainties.UFloat]],
                                   m: Union[float, uncertainties.UFloat],
                                   c: Union[float, uncertainties.UFloat]) \
            -> Union[float, uncertainties.UFloat, List[float], List[uncertainties.UFloat]]:
        """
        Inverse of the straight line function so that we can get x from y: x = f(y, m, c) = (y-c)/m
        """
        return np.divide(np.subtract(y, c), m)

    @classmethod
    def _const_from_straight_line_func(cls,
                                       x: Union[float, uncertainties.UFloat],
                                       y: Union[float, uncertainties.UFloat],
                                       m: Union[float, uncertainties.UFloat]) -> Union[float, uncertainties.UFloat]:
        """
        Calculates the const of a straight line function if given an (x, y) point and the slope (m).
        c = y - mx
        """
        return np.subtract(y, np.multiply(m, x))

    def _calculate_plot_points(self, ax: Axes, y_shift: float = 0.0) -> Tuple[List[float], List[float]]:
        """
        Called by super() when drawing the Fit.  Tell it what data points to draw.
        """
        return self._x_endpoints, np.add(self._y_endpoints, y_shift)
