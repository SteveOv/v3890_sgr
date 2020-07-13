import numpy as np
from typing import List, Union
import uncertainties
from uncertainties import ufloat
from fitting import FitBase, StraightLineFit


class StraightLineLogXFit(StraightLineFit):
    """
    A straight line, linear least squares fit to a range of data based on the x values being on a log10 scale.
    The slope will be defined and managed in the y-Vs-log10(x) domain. Client calls for calculating/interacting/querying
    remains in the linear x domain.  Linear x values are automatically translated to/from the log10 values as needed.
    """

    def __str__(self) -> str:
        if self.has_fit:
            text = f"{self.__class__.__name__}[{self.id}] covering x in ({self.range_from}, {self.range_to}): "
            text += f"y = [{self.slope:.6fP} * log10(x)] + {self.const:.6fP}"
            text += F"\n\tGiving a power law: {self.power_law}"
        else:
            text = super().__str__()
        return text

    @property
    def power_law(self) -> str:
        """
        Restates this fit's slope as a power law, assuming that the slope is a straight line fit on log(y)/log(x) data.
        """
        if self.has_fit:
            power_slope = self.slope / -2.5
            law = F"$F \\propto t^{{\\alpha_{{{self.id}}}}}, \\alpha_{{{self.id}}} = {power_slope:.5fP}$"
        else:
            law = "<No slope: insufficient data to fit line>"
        return law

    @classmethod
    def fit_to_data(
            cls, id: int, xi: List[float], yi: List[float], dyi: List[float], range_from: float, range_to: float) \
            -> FitBase:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
        """
        # Prior to fitting we need to convert the xi values to their log equivalent
        fit = super().fit_to_data(id, np.log10(xi), yi, dyi, np.log10(range_from), np.log10(range_to))

        # Once the fit's been calculated with the log(x) values, revert the public/descriptive x values back to linear
        fit._range_from = range_from
        fit._range_to = range_to

        # Leave the private x_endpoints at their log10 values as these are used when interacting with the fit,
        # which has been created in terms of log(x), so any calculations/searches need to remain in these terms.
        return fit

    @classmethod
    def copy(cls, src: FitBase, x_shift: float = 0, y_shift: float = 0, new_id: int = None) -> FitBase:
        """
        Makes a safe copy of this Fit instance (so the data really is a copy, not a reference)
        while optionally applying x/y shifts and a new id.
        """
        cp = super().copy(src, x_shift, y_shift, new_id)

        # Over and above what the superclass does, if we have any shifts then we have to make allowance for the
        # fact that the data defining the slope is in "log10(x)" form, and therefore the x-shift is not linear.
        if x_shift != 0 and src.has_fit and isinstance(src, cls) and isinstance(cp, cls):
            # We need to "un-log", shift and then "re-log" the data.
            cp._endpoints_x = cls._shift_on_log10_values(src.endpoints_x, x_shift)

            # An x-shift will change the parameters of the slope.  The super() has applied a linear shift
            # which works OK in the y-axis but not in the x-axis.  Calculate new slope based on revised (x,y) points.
            slope = ufloat(np.divide(cp.endpoints_y[1] - cp.endpoints_y[0], cp.endpoints_x[1] - cp.endpoints_x[0]),
                           src.slope.std_dev)
            const = cls._const_from_straight_line_func(cp.endpoints_x[0], cp.endpoints_y[0], slope)
            cp._fit_params = (slope, const)

            test_y = cls._y_from_straight_line_func(cp.endpoints_x, cp.slope.nominal_value, cp.const.nominal_value)
            assert all(cp.endpoints_y) == all(test_y)
        return cp

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        """
        Calculate the residuals - the y-difference between the y data points
        and the slope as defined by this instance's slope and const
        """
        x, y = super().calculate_residuals(np.log10(xi), yi)
        if x is not None:
            x = np.power(10, x).tolist()
        return x, y

    def find_peak_y_value(self, is_minimum: bool = False) -> (float, uncertainties.UFloat):
        """
        Find the peak y value of this Fit.  Returns a tuple of the x value and y_value where found.
        The is_minimum argument may be set to true, in which case the peak is considered the minimum y_value (not max)
        """
        at_x, peak_y = super().find_peak_y_value(is_minimum)
        if at_x is not None:
            at_x = np.power(10, at_x)
        return at_x, peak_y

    def find_x_value(self, y_value: uncertainties.UFloat) -> float:
        """
        Finds the value of the independent (x) variable at the requested dependent (y) variable based on the nominal
        value of the the dependent variable. Handles the fact that the fit is calculated against log(x) values.
        """
        x_value = super().find_x_value(y_value)
        if x_value is not None:
            x_value = np.power(10, x_value)
        return x_value

    def find_y_value(self, x_value: float) -> uncertainties.UFloat:
        """
        Finds the value of the dependent (y) variable at the requested independent (x) variable
        """
        return super().find_y_value(np.log10(x_value))

    @classmethod
    def _shift_on_log10_values(cls, log_data: Union[float, List[float]], shift: float = 0) -> Union[float, List[float]]:
        """
        Apply a linear shift to the data which has been encoded as log10() values; "un"-log, shift then "re"-log
        """
        data = np.power(10, log_data)
        return np.log10(np.add(data, shift)).tolist()