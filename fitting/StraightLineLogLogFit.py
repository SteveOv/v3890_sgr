from fitting.StraightLineLogXFit import *


class StraightLineLogLogFit(StraightLineLogXFit):
    """
    A straight line, linear least squares fit to a range of data based on the x & y values being on a log10 scale.
    The slope will be defined and managed in the log10(y) Vs log10(x) domain.
    Client calls for calculating/interacting/querying remains in the linear (x, y) domain.
    Linear (x, Y) values are automatically translated to/from the log10 values as needed.

    Derived from StraightLineLogXFit which manages converting x values to/from log(x) as needed.
    This subclass need only look after converting y values to/from log(y)
    """

    @classmethod
    def fit_to_data(cls, id: int, xi: List[float], yi: List[float],
                    dxi: List[float] = None, dyi: List[float] = None,
                    range_from: float = None, range_to: float = None) -> Fit:
        """
        Factory method to create a Fit based on the passed data (xi, yi and delta yi) over the requested range of xi.
        """
        # Prior to fitting we need to convert the yi/dyi values to their log equivalent (xi values done by super())
        log_yi = np.log10(yi)
        log_dyi = np.log10(dyi)
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

    def draw_on_ax(self, ax: Axes, color: str, line_width: float = 0.5, label: str = None, y_shift: float = 0):
        """
        Gets the FitSet to draw itself onto the passed matplotlib ax
        """
        x_ep = np.power(10, self._x_endpoints)
        y_ep = np.power(10, self._y_endpoints)
        return ax.plot(x_ep, np.add(y_ep, y_shift), label=label,
                       color=color, linestyle="-", linewidth=line_width, alpha=1, zorder=2, antialiased=True)

    def calculate_residuals(self, xi: List[float], yi: List[float]) -> (List[float], List[float]):
        """
        Calculate the residuals - the y-difference between the y data points and the slope as defined by
        this instance's slope and const.  Note, as the fit was made against log(yi) data the residuals are
        of log(y) and need to be plotted on a linear axis marked up as log(y).
        """
        log_yi = np.log10(yi)
        res_x, log_res_y = super().calculate_residuals(xi, log_yi)
        return res_x, log_res_y
