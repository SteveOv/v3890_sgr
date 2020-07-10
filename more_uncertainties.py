import numpy as np
import uncertainties
from uncertainties import ufloat, unumpy


def log10(x):
    """
    Find the log10 of x when x is a ufloat
    """
    if isinstance(x, uncertainties.UFloat):
        log_x = ufloat(np.log10(x.nominal_value), np.divide(x.std_dev, x.nominal_value))
    else:
        log_x = np.log10(x)

    return log_x


def undo_log10(x):
    """
    Find the inverse/reverse of log10 of x - undo it
    """
    return 10 ** x
