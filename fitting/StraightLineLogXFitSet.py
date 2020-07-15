from typing import List
from fitting import Fit, FitSet, StraightLineLogXFit


class StraightLineLogXFitSet(FitSet):
    """
    A set of StraightLineLogXFit types used to fit a range of data
    It handles the fact that the x-axis is represented in log10(x) form
    """

    @classmethod
    def _create_fitted_fit_on_data(
            cls, id: int, xi: List[float], yi: List[float], dyi: List[float], from_xi: float, to_xi: float) -> Fit:
        """
        Custom factory method for creating the fits associated with this set.
        """
        return StraightLineLogXFit.fit_to_data(id, xi, yi, dxi=None, dyi=dyi, range_from=from_xi, range_to=to_xi)
