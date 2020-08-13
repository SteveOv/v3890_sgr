import numpy as np

# Gives us numeric values with built in support for uncertainties
import uncertainties
from uncertainties import ufloat


def absolute_magnitude_from_t2(t2):
    """
    Uses the MMRD t_2 relation (from the TDA course notes) to calculate an absolute magnitude
    """
    return _absolute_magnitude_from_coefficients(
        ufloat(-11.32, 0.44), ufloat(2.55, 0.32), t2, 'MMRD t_2 relation from TDA notes')


def absolute_magnitude_from_t3(t3):
    """
    Uses the MMRD t_3 relation (from the TDA course notes) to calculate an absolute magnitude
    """
    return _absolute_magnitude_from_coefficients(
        ufloat(-11.99, 0.56), ufloat(2.54, 0.35), t3, 'MMRD t_3 relation from TDA notes')


def absolute_magnitude_from_t2_fast_nova(t2):
    """
    Uses the MMRD t_2 relation for a fast nova (Downes & Duerbeck, 2000) as used by Schaefer (2010)
    """
    return _absolute_magnitude_from_coefficients(
        ufloat(-10.79, 0), ufloat(1.53, 0), t2, "MMRD t_2 'A' class relation from Downes & Duerbeck (2000)")


def absolute_magnitude_from_t3_fast_nova(t3):
    """
    Uses the MMRD t_3 relation for a fast nova (Downes & Duerbeck, 2000) as used by Schaefer (2010)
    """
    return _absolute_magnitude_from_coefficients(
        ufloat(-11.26, 0), ufloat(1.58, 0), t3, "MMRD t_3 'A' class relation from Downes & Duerbeck (2000)")


def _absolute_magnitude_from_coefficients(coefficient0, coefficient1, t, relation_name):
    if isinstance(t, uncertainties.UFloat):
        abs_mag = coefficient0 + (coefficient1 * _log_on_ufloat(t))
    else:
        abs_mag = coefficient0 + (coefficient1 * np.log(t))
    print(F"Using the {relation_name}: M_V = {coefficient0:.4f} + {coefficient1:.4f} * log({t:.4f}) = {abs_mag:.4f}")
    return abs_mag


def _log_on_ufloat(x):
    """
    Perform a log on a ufloat, returning another ufloat.
    Doesn't seem to have a log function in its libraries.
    """
    log = np.log(x.nominal_value)
    sigma = np.divide(x.std_dev, x.nominal_value)
    return ufloat(log, sigma)
