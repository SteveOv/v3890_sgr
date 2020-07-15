from abc import ABC, abstractmethod
from typing import List
from fitting import Fit


class FittedFit(Fit, ABC):
    """
    Base class for more complex fits, where they have to be fitted to data.
    """
    @classmethod
    @abstractmethod
    def fit_to_data(cls, id: int, xi: List[float], yi: List[float],
                    dxi: List[float] = None, dyi: List[float] = None,
                    from_xi: float = None, to_xi: float = None) -> Fit:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
        """
        pass
