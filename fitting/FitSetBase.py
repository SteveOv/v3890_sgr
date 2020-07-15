from abc import ABC, abstractmethod
from typing import List, Union
from pandas import DataFrame
import copy
import uncertainties
import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from fitting import FitSetBase
from fitting.FitBase import FitBase


class FitSetBase(ABC):
    """
    Base class for a set of fits to a range of data
    """

    # TODO: Python 3 does support some form of generics so look at reworking this as a generic type.
    #       This should make the logic around the Fits factory easier, and we'll require less from any subclass.

    def __init__(self, fits: List[FitBase], breaks: List[float]):
        self._fits = fits
        self._breaks = breaks

    def __iter__(self) -> [FitBase]:
        return self._fits.__iter__()

    def __next__(self) -> FitBase:
        return self._fits.__next__()

    def __str__(self) -> str:
        text = f"{type(self).__name__}: breaks = {self.breaks}".replace("\n", "")
        for fit in self:
            text += F"\n{fit}"
        return text

    @property
    def breaks(self) -> List[float]:
        return self._breaks

    @classmethod
    def copy(cls, source: FitSetBase, x_shift: float = 0, y_shift: float = 0) -> FitSetBase:
        """
        Creates a copy of this fit set and optionally applies a y axis offset to the contained fits
        """
        fits = []
        for fit in source:
            fits.append(type(fit).copy(fit, x_shift, y_shift))
        new_set = cls(fits, np.add(copy.copy(source.breaks), x_shift))
        print(f"Copied {cls.__name__} while applying x_shift = {x_shift} and y_shift = {y_shift}.\n{new_set} to Fits")
        return new_set

    @classmethod
    def fit_to_data(cls, df: DataFrame, x_col: str, y_col: str, y_err_col: str,
                    breaks: List[Union[float, str]], start_id: int = 0)\
            -> FitSetBase:
        """
        Factory method for a fit set.  Will create a set of fits to the passed data (x, y and delta y)
        based on the list of breaks.  Each fit will be labelled with a subscript starting at start_id.
        """
        fits = []
        ranges = cls._ranges_from_breaks(df[x_col], breaks)
        for range in ranges:
            from_xi = range[0]
            to_xi = range[1]

            # Must have at least two data points to calculate the best fit line
            range_df = df.query(F"{x_col}>={from_xi}").query(F"{x_col}<={to_xi}").sort_values(by=x_col)
            if len(range_df) > 1:
                fit = cls._on_new_fit(start_id, range_df[x_col], range_df[y_col], range_df[y_err_col], from_xi, to_xi)
            else:
                fit = cls._on_new_fit(start_id, [], [], [], from_xi, to_xi)

            fits.append(fit)
            start_id += 1

        fit_set = cls(fits, breaks)
        return fit_set

    def draw_on_ax(self, ax: Axes, color: str, line_width: float = 0.5, label: str = None, y_shift: float = 0):
        """
        Gets the FitSet to draw itself onto the passed matplotlib ax
        """
        for fit in self:
            fit.draw_on_ax(ax, color, line_width=line_width, label=label, y_shift=y_shift)
            label = None  # Make sure we only set the label once otherwise it will be duplicated in any legend
        return

    def calculate_residuals(self, df: DataFrame, x_col: str, y_col: str) -> (List[float], List[float]):
        """
        Calculates the residuals for the passed data against the associated fits.  Specifically for
        'post processing' to derive residuals for these data against fits which were created from other data.
        Returns an array of [{'x': [], 'y': []}] (an item per fit)
        """
        x_res = []
        y_res = []
        for fit in self:
            if fit.has_fit:
                df_fit = df.query(F"{x_col} >= {fit.range_from} and {x_col} <= {fit.range_to}")
                x, y = fit.calculate_residuals(df_fit[x_col].to_list(), df_fit[y_col].to_list())
                x_res += x
                y_res += y

        return x_res, y_res

    def find_peak_y_value(self, is_minimum: bool = False) -> (float, uncertainties.UFloat):
        """
        Finds the peak y_value indicated by the passed fits, and for what x_value it occurs.
        is_minimum indicates whether the peak will be the minimum value (True) or maximum (False)
        returns (x: float, y: UFloat)
        """
        peak_y = None
        at_x = 0
        for fit in self:
            is_at, new_peak = fit.find_peak_y_value(is_minimum)
            if peak_y is None or (is_minimum and new_peak < peak_y) or (is_minimum is False and new_peak > peak_y):
                peak_y = new_peak
                at_x = is_at

        return at_x, peak_y

    def find_x_value(self, y_value: uncertainties.UFloat) -> float:
        """
        Uses the fit set to calculate the first x_value (no uncertainty) which will have the passed y_value
        """
        x_value = None
        for fit in self:
            x_value = fit.find_x_value(y_value)
            if x_value is not None:
                break
        return x_value

    def find_y_value(self, x_value: float) -> uncertainties.UFloat:
        """
        Uses the fit set to calculate the y_value (with uncertainty) at the requested x_value
        """
        y_value = None
        for fit in self:
            y_value = fit.find_y_value(x_value)
            if y_value is not None:
                break
        return y_value

    @classmethod
    @abstractmethod
    def _on_new_fit(cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float):
        """
        To be implemented by concrete subclasses which will know which Fit to create.
        """
        pass

    @classmethod
    def _ranges_from_breaks(cls, xi: List[float], breaks: List[Union[float, str]] = None) -> [(float, float)]:
        """
        Turn the passed break points (each a single xi value) into ranges over which fits can be calculated.
        The ranges extend between each break point and extend out to the min and max limits of the data.

        Example: if data covers xi values in the range of 0 to 10 and break points
        are given as [3, 7], then the ranges calculated will be [(0, 3), (3, 7), (7, 10)]
        There should always be 1 more range defined than there are break points
        """
        if xi is not None and len(xi) > 0:
            min_xi = min(xi)
            max_xi = max(xi)

            # Turn the breaks into ranges.  Step through creating ranges from contiguous numeric breaks.
            ranges = []
            if breaks is not None:
                for ix in np.arange(0, len(breaks) - 1):
                    brk = breaks[ix]
                    if isinstance(brk, str):  # Break is a string, which indicates an instruction
                        print(F"{cls.__name__}: Encountered the instruction '{brk}' parsing breaks to ranges.")
                        if str.isspace(brk):
                            # A space(s) instructs us to skip a range: don't create a range over the surrounding values.
                            # Also applies at extremes of breaks: stops creation of extra ranges where (xi) values
                            # extend beyond the breaks specified.
                            # So breaks [1, 2, " ", 3, 4] become ranges [(1, 2), (3, 4)]
                            pass
                        else:
                            # Currently, no other instructions supported
                            pass
                    else:  # OK it's numeric.
                        # First item - see if we need to prepend a range to cover data preceding the first break.
                        if ix == 0 and min_xi < brk:
                            ranges.append((min_xi, brk))

                        if ix < (len(breaks) - 1):
                            # Not the last item, so what's coming up next?
                            if not isinstance(breaks[ix + 1], str):
                                # Next break is also numeric, so we create a range
                                ranges.append((brk, breaks[ix + 1]))
                        elif max_xi > brk:
                            # Last item - see if we need to append a range to cover the data beyond the last break.
                            ranges.append((brk, max_xi))

        return ranges

