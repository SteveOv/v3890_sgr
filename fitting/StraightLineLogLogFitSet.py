from typing import List
import numpy as np
from pandas import DataFrame
from fitting.FitSetBase import FitSetBase
from fitting.FitBase import FitBase
from fitting.StraightLineLogLogFit import StraightLineLogLogFit


class StraightLineLogLogFitSet(FitSetBase):
    """
    A set of StraightLineLogLogFit types used to fit a range of data
    It handles the fact that the x-axis is represented in log10(x) form
    """

    @classmethod
    def copy(cls, source: FitSetBase, x_shift: float = 0, y_shift: float = 0) -> FitSetBase:
        """
        Creates a copy of this fit set and optionally applies a y axis offset to the contained fits
        """
        new_set = super().copy(source, x_shift, y_shift)

        # Have to re-do any x-shift for the breaks in this set as the x values are held as log(x) value
        # and the value of the shift is not linear
        if x_shift != 0:
            breaks = np.power(10, source.breaks)
            new_set._breaks = np.log10(np.add(breaks, x_shift))
        return new_set

    @classmethod
    def fit_to_data(cls, df: DataFrame, x_col: str, y_col: str, y_err_col: str,
                    breaks: List[float], breaks_are_logs: bool = False, start_id: int = 0) \
            -> FitSetBase:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
        """
        # Override default behaviour as we need to make sure the breaks are in terms of log x-values before proceeding
        if not breaks_are_logs:
            print(f"{cls.__name__}.fit_to_data(breaks={breaks}).\nTold they're not log(x), so will take logs first.")
            breaks = np.log10(breaks)
        return super().fit_to_data(df, x_col, y_col, y_err_col, breaks, start_id)

    @classmethod
    def _on_new_fit(cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float)\
            -> FitBase:
        """
        Custom factory method for creating the fits associated with this set.
        """
        return StraightLineLogLogFit.fit_to_data(id, xi, yi, dyi, from_xi, to_xi)
