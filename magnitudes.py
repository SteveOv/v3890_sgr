import numpy as np 
import pandas as pd 

# Gives us numeric values with built in support for uncertainties
from uncertainties import ufloat


def calculate_t0_from_fits(fits):
    """
    Find the time of the peak (minimum) apparent magnitude from the passed slopes
    """
    mag0 = None
    for fit in reversed(fits):
        if fit['slope'] != 0:
            # The slopes after maximum measure a decline, so the peak will be the initial value in one of the slopes
            min_mag = fit['y'][0]
            if mag0 is None or min_mag < mag0:
                t0 = ufloat(time_from_log10_time(fit['x'][0]), 0)

    return t0


def distance_from_magnitudes(apparent, absolute, extinction=0):
    """
    Uses a re-arranged distance modulus calculation to calculate the 
    distance to an object with the passed apparent and absolute magnitude
    while taking into account the optional extinction value
    """
    return 10**(0.2 * (apparent - absolute + 5 - extinction))


def extinction_from_color(excess, galactic_extinction=3.1):
    """
    Calculate the extinction from the passed E(B-V) excess and R_V galactic extinction.
    """
    return excess * galactic_extinction


def calculate_peak_magnitude_and_t0(slopes, te=ufloat(0, 0)):
    """
    Find the time of the peak (minimum) apparent magnitude from the passed slopes
    """   
    mag0 = None
    for slope in reversed(slopes):
        if slope['slope'] != 0:
            # The slopes measure a decline, so the peak will be the initial value in one of the slopes
            min_mag = slope['y'][0]
            if mag0 is None or min_mag < mag0:

                # TODO: Uncertainty for the magnitude as derived from the slope.  Do we use the slope's uncertainty?
                mag0 = ufloat(min_mag, slope['slope'].std_dev)
                t0 = ufloat(time_from_log10_time(slope['x'][0]), 0) - te

    return mag0, t0


def calculate_t2_and_t3(mag0, t0, fits):
    """
    Use the passed slopes data to find the peak magnitude and then calculate the t2 and t3 values

    fits - the set of fitted slopes to use
    """
    mag2 = mag0 + 2
    mag3 = mag0 + 3
    t2 = t3 = ufloat(0, 0)
    for fit in fits:
        # Ignore any fits before the one containing the peak magnitude
        if fit['slope'] != 0 and time_from_log10_time(ufloat(max(fit['x']), 0)) > t0:
            min_mag = min(fit['y'])
            max_mag = max(fit['y'])

            # The fit's (x,y) values have no uncertainty (they are used for plotting) whereas the slope and const do
            # TODO; for now find the range containing the nominal of desired magnitude
            if mag2.nominal_value >= min_mag and mag2.nominal_value <= max_mag:
                # mag2 is within this slope, find the log(t) when it occurred
                t2 = _calculate_time_at_mag_from_slope(mag2, fit, t0)

            if mag3.nominal_value >= min_mag and mag3.nominal_value <= max_mag:
                t3 = _calculate_time_at_mag_from_slope(mag3, fit, t0)
                break
    return t2, t3


def time_from_log10_time(log_t):
    return 10 ** log_t


def _calculate_time_at_mag_from_slope(mag, slope, t0):
    """
    Estimate the time (t) when the requested magnitude is reached on the passed slope.
    # when:     mag = m*log(t_mag) + c
    # then:     log(t_mag) = (mag-c)/m
    # giving:   t_mag = 10^{(mag-c)/m}
    # finally:  t = t_mag - t0
    """
    m = slope['slope']
    c = slope['const']
    t_mag = time_from_log10_time((mag - c) / m)
    t = t_mag - t0

    # TODO: work out the expression for the uncertainty
    return t
