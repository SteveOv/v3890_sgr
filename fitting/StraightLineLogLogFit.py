import numpy as np
from typing import List, Union
from uncertainties import ufloat
from fitting import FitBase, StraightLineFit, StraightLineLogLogFit


class StraightLineLogLogFit(StraightLineFit):
    """
    A straight line, linear least squares fit to a range of data where the x values are on a log scale.
    """

    def __str__(self) -> str:
        text = super().__str__()
        if self.has_fit:
            text += F"\n\tGiving a power law: {self.power_law}"
        return text

    @property
    def power_law(self) -> str:
        """
        Restates the passed slope data as a power law,
        assuming that the fitted slope is a straight line fit on log(day)/mag data.
        """
        if self.has_fit:
            law = F"$F \\propto t^{{\\alpha_{{{self.id}}}}}, \\alpha_{{{self.id}}} = {self.slope / -2.5:.5fP}$"
        else:
            law = "<No slope: insufficient data to fit line>"
        return law

    @classmethod
    def copy(cls, src: FitBase, x_shift: float = 0, y_shift: float = 0, new_id: int = None) -> FitBase:
        """
        Makes a safe copy of this Fit instance (so the data really is a copy, not a reference)
        while optionally applying x/y shifts and a new id.
        """
        cp = super().copy(src, x_shift, y_shift, new_id)
        if isinstance(src, StraightLineLogLogFit) and isinstance(cp, StraightLineLogLogFit) \
           and src.has_fit and x_shift != 0:
            # Over and above what the superclass does, if we have any shifts then we have to make allowance for the
            # fact that the data underlying the slope is in log10(x) form, and therefore the x-shift is not linear.
            cp._range_from = cls._shift_within_log10(src.range_from, x_shift)
            cp._range_to = cls._shift_within_log10(src.range_to, x_shift)
            cp._x_points = cls._shift_within_log10(src.x_points, x_shift)

            # An x-shift will change the parameters of the slope.  The super() has applied a linear shift
            # which works OK in the y-axis but not in the x-axis.  Calculate new slope based on revised (x,y) points.
            slope = ufloat(np.divide(cp.y_points[1]-cp.y_points[0], cp.x_points[1]-cp.x_points[0]), src.slope.std_dev)
            const = cls._const_from_straight_line_func(cp.x_points[0], cp.y_points[0], slope)
            cp._fit_params = (slope, const)

            test_y = cls._y_from_straight_line_func(cp.x_points, cp.slope.nominal_value, cp.const.nominal_value)
            assert all(cp.y_points) == all(test_y)
        return cp

    @classmethod
    def _shift_within_log10(cls, log_data: Union[float, List[float]], shift: float = 0) -> Union[float, List[float]]:
        """
        Apply a linear shift to the data which has been encoded as log10() values
        """
        # "un"-log, shift then "re"-log
        data = np.power(10, log_data)
        return np.log10(np.add(data, shift))
