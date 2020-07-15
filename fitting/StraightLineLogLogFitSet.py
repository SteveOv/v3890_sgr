from fitting.FitSetBase import FitSetBase
from fitting.StraightLineLogLogFit import *


class StraightLineLogLogFitSet(FitSetBase):
    """
    A set of StraightLineLogLogFit types used to fit a range of data
    It handles the fact that both the x- and y-axis are represented in Log form.
    """

    @classmethod
    def _on_new_fit(cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float)\
            -> FitBase:
        """
        Custom factory method for creating the fits associated with this set.
        """
        return StraightLineLogLogFit.fit_to_data(id, xi, yi, dyi, from_xi, to_xi)
