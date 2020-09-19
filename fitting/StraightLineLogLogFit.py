from fitting.StraightLineLogXFit import *
from utility import uncertainty_math as um

class StraightLineLogLogFit(StraightLineLogXFit):
    """
    A straight line, linear least squares fit to a range of data based on the x & y values being on a log10 scale.
    The slope will be defined and managed in the log10(y) Vs log10(x) domain.
    Client calls for calculating/interacting/querying remains in the linear (x, y) domain.
    Linear (x, Y) values are automatically translated to/from the log10 values as needed.

    Derived from StraightLineLogXFit which manages converting x values to/from log(x) as needed.
    This subclass need only look after converting y values to/from log(y)
    """

    @property
    def alpha(self) -> UFloat:
        """
        The alpha value of the slope power law as expressed as t^alpha
        """
        # The slope here is not propto 1/-2.5 as here we measure log counts (mag are inverted hence the minus).
        # In this case the slope is propto 1/2.5
        return self.slope / ufloat(2.5, 0)

    @classmethod
    def fit_to_data(cls, id: int, xi: List[float], yi: List[float],
                    dxi: List[float] = None, dyi: List[float] = None,
                    range_from: float = None, range_to: float = None) -> Fit:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
        """
        # Prior to fitting we need to convert the yi/dyi values to their log equivalent (xi values done by super())
        log_yi = np.log10(yi)
        log_dyi = np.log10(dyi) if dyi is not None else None
        fit = super().fit_to_data(id, xi, log_yi, dxi=dxi, dyi=log_dyi, range_from=range_from, range_to=range_to)

        # Leave the private _x/_y_endpoints at their log10 values as these are used when interacting with the fit, which
        # has been created in terms of log(y) v log(x), so any calculations/searches need to remain in these terms.
        return fit

    @classmethod
    def copy(cls, src: Fit, x_shift: float = 0, y_shift: float = 0, new_id: int = None) -> Fit:
        """
        Makes a safe copy of this Fit instance (so the data really is a copy, not a reference)
        while optionally applying x/y shifts and a new id.
        """
        cp = super().copy(src, x_shift, y_shift, new_id)
        if y_shift:
            # TODO: Will need to revisit this to handle a y-shift over the log(y) data (super handles log(x) OK)
            pass
        return cp

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        """
        Calculate the residuals - the y-difference between the y data points and the slope as defined by
        this instance's slope and const.  Note, as the fit was made against log(yi) data the residuals are
        of log(y) and need to be plotted on a linear axis marked up as log(y).
        """
        log_yi = np.log10(yi)
        res_x, log_res_y = super().calculate_residuals(xi, log_yi)
        return res_x, log_res_y

    def find_peak_y_value(self, is_minimum: bool = False) -> (float, uncertainties.UFloat):
        """
        Find the peak y value of this Fit.  Returns a tuple of the x value and y_value where found.
        The is_minimum argument may be set to true, in which case the peak is considered the minimum y_value (not max)
        """
        at_x, peak_y = super().find_peak_y_value(is_minimum)
        # Super() is LogX fit and handles log/de-logging the x-axis but not the y-axis, so we do it here.
        if peak_y is not None:
            peak_y = np.power(10, peak_y)
        return at_x, peak_y

    def find_x_value(self, y_value: uncertainties.UFloat) -> float:
        """
        Finds the value of the independent (x) variable at the requested dependent (y) variable based on the nominal
        value of the the dependent variable. Handles the fact that the fit is calculated against log(x) values.
        """
        # Transform the linear y_value into the log10 form underlying (super() is logX so only expects x-axis logs)
        log_y = ufloat(*um.log10(y_value.nominal_value, y_value.std_dev))
        return super().find_x_value(log_y)

    def find_y_value(self, x_value: float) -> uncertainties.UFloat:
        """
        Finds the value of the dependent (y) variable at the requested independent (x) variable
        """
        # Super handles logX values but is unaware of the log y values
        log_y = super().find_y_value(x_value)
        linear_y = ufloat(*um.power(10, 0, log_y.nominal_value, log_y.std_dev)) if log_y is not None else None
        return linear_y

    def _calculate_plot_points(self, ax: Axes, y_shift: float = 0.0) -> Tuple[List[float], List[float]]:
        """
        Called by super() when drawing the Fit.  Tell it what data points to draw.
        """
        x_ep = np.power(10, self._x_endpoints)
        y_ep = np.power(10, self._y_endpoints)
        return x_ep, np.add(y_ep, y_shift)
