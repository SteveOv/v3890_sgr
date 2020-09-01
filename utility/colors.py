import numpy as np
from numpy import ndarray
from utility import uncertainty_math as um


def color_from_magnitudes(mag_1, mag_1_err, mag_2, mag_2_err):
    """
    Calculate a color from the passed magnitudes (with uncertainties).
    Based on equivalent
        (B-V)_obs = mag(B) - mag(V)
    """
    return um.subtract(mag_1, mag_1_err, mag_2, mag_2_err)


def color_excess_from_colors(obs_color, obs_color_err, int_color, int_color_err):
    """
    Calculate a color excess as the difference between the observed color and the intrinsic color.
    """
    return um.subtract(obs_color, obs_color_err, int_color, int_color_err)


def intrinsic_color_from_observed_color_and_excess(obs_color, obs_color_err, color_excess, color_excess_err):
    """
    Calculate the intrinsic color from the passed observed color and color excess.
    Based on
        color_excess = obs_color - intrinsic_color
    therefore
        intrinsic_color = obs_color - color_excess
    """
    return um.subtract(obs_color, obs_color_err, color_excess, color_excess_err)

