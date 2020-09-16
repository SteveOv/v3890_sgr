from typing import Tuple
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


def E_BV_from_E_gr_Jester(egr: float, egr_err: float) -> Tuple[float, float]:
    """
    Convert a SDSS E(g-r) color excess to a J-C E(B-V) color excess.
    Based on the transformations in Table 1 of Jester et al. (2005) AJ, 130,3
    In this case, for stars with Rc-Ic < 1.15
    """
    # Conversion based on;
    #       B-V = 0.98*(g-r) + 0.22 (RMS residual 0.04)
    #
    B_V, B_V_err = um.add(*um.multiply(0.98, 0, egr, 0), 0.22, 0)
    B_V_err = um.multiply(0.04, 0, B_V, B_V_err)
    return B_V_err


def E_BV_from_E_gr_Jordi_populationI(egr: float, egr_err: float) -> Tuple[float, float]:
    """
    Convert a SDSS E(g-r) color excess to a J-C E(B-V) color excess.
    Based on the transformations in Table 3 of Jordi et al. (2006) A&A, 460
    for population I stars and interpreted on the SDSS DR13 site; 
        https://www.sdss.org/dr13/algorithms/sdssUBVRITransform/#Jordi2006
    """
    # B-g = (0.312 pm 0.003)*(g-r) + (0.219 pm 0.002)
    # V-g = (-0.573 pm 0.002)*(g-r) - (0.016 pm 0.002)
    #
    # (B-g)-(V-g) = (0.312 pm 0.003)*(g-r) + (0.219 pm 0.002) + (0.573 pm 0.002)*(g-r) + (0.016 pm 0.002)
    # B-V = (0.885 pm 0.004)*(g-r) + (0.235 pm 0.003)
    #
    B_V, B_V_err = um.add(*um.multiply(0.885, 0.004, egr, egr_err), 0.235, 0.003)
    return B_V, B_V_err


def E_BV_from_E_gr_Jordi_metal_poor(egr: float, egr_err: float) -> Tuple[float, float]:
    """
    Convert a SDSS E(g-r) color excess to a J-C E(B-V) color excess.
    Based on the transformations in Table 3 of Jordi et al. (2006) A&A, 460
    for metal poor population II stars and interpreted on the SDSS DR13 site;
        https://www.sdss.org/dr13/algorithms/sdssUBVRITransform/#Jordi2006
    """
    # B-g = (0.349 pm 0.009)*(g-r) + (0.245 pm 0.006)
    # V-g = (-0.569 pm 0.007)*(g-r) + (0.021 pm 0.004)
    #
    # (B-g)-(V-g) = (0.349 pm 0.009)*(g-r) + (0.245 pm 0.006) + 0.569 pm 0.007)*(g-r) - (0.021 pm 0.004)
    # B-V = (0.918 pm 0.011)*(g-r) + (0.224 pm 0.007)
    #
    B_V, B_V_err = um.add(*um.multiply(0.918, 0.011, egr, egr_err), 0.224, 0.007)
    return B_V, B_V_err


def E_BV_from_E_gr_Lupton(egr: float, egr_err: float) -> Tuple[float, float]:
    """
    Convert a SDSS E(g-r) color excess to a J-C E(B-V) color excess.
    Conversions between B and g and V and g are taken from SDSS III website
    http://www.sdss3.org/dr8/algorithms/sdssUBVRITransform.php
    which in turn takes values from Lupton, 2005.
    """
    # Conversion based on;
    # B = g + 0.3130(g-r)-0.2271 +/- 0.0107
    # V = g - 0.5784(g-r)-0.0038 +/- 0.0054
    #
    # B-V = 0.3130(g-r) + 0.2271 + 0.5784(g-r) + 0.0038
    # d(B-V) = sqrt(0.0107^2 + 0.0054^2)
    #
    B_V, B_V_err = um.add(*um.multiply(0.8914, 0, egr, egr_err), 0.2309, 0)
    B_V_err = um.uncertainty_add_or_subtract(B_V_err, 0.0119854)
    return B_V, B_V_err