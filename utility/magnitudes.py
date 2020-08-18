from typing import Dict, Tuple
from utility import uncertainty_math as unc

mag_ab_correction_factors = {
    # FROM LJMU Website
    "B": -0.1,
    "V": 0,
    "R": 0.2,
    "I": 0.45,

    # From Breeveld (2010) Swift-UVOT-CALDDB-16-R01
    "UVM2": 1.69,
    "UVW2": 1.73
}


def mag_ab_from_mag_vega(mag, mag_err, band: str = "V"):
    mag_ab, mag_ab_err = unc.add(mag, mag_err, mag_ab_correction_factors[band], 0)
    return mag_ab, mag_ab_err


def mag_vega_from_mag_ab(mag_ab, mag_ab_err, band: str = "V"):
    mag_vega, mage_vega_err = unc.subtract(mag_ab, mag_ab_err, mag_ab_correction_factors[band], 0)
    return mag_vega, mage_vega_err


def flux_density_jy_from_mag_ab(mag_ab, mag_ab_err=0):
    """
    Calculate the flux, in units of Jansky, of the passed mag(AB)

    Based on the standard definition of the magnitude system, where monochromatic flux (in erg/s/cm^2/Hz)
                  f = 10^( -0.4( mag(AB) + 48.60 ) )
    if you work through that 1 Jy = 10^-23, so f [Jy] = f/10^-23, you get
                  f = 10^( 0.4( 8.9 - mag(AB) ) ) Jy
    """
    exponent, exponent_err = unc.multiply(0.4, 0, *unc.subtract(8.9, 0, mag_ab, mag_ab_err))
    return unc.power(10, 0, exponent, exponent_err)


def flux_density_cms_from_mag_ab(mag_ab, mag_ab_err=0):
    """
    Calculate the flux, in units of erg/s/cm^2/Hz, of the passed mag(AB) value.

    Based on the standard definition of the magnitude system, where monochromatic flux (in erg/s/cm^2/Hz)
    gives magnitude (Oke, 1974)
                  mag(AB) = -2.5 log(f) - 48.60
    therefore
                  f = 10^( -0.4( mag(AB) + 48.60 ) )
    """
    exponent, exponent_err = unc.multiply(-0.4, 0, *unc.add(mag_ab, mag_ab_err, 48.60, 0))
    return unc.power(10, 0, exponent, exponent_err)


def mag_ab_from_flux_density_cms(flux, flux_err):
    """
    Calculate the flux, in units of erg/s/cm^2/Hz, of the passed mag(AB) value.

    Based on the standard definition of the magnitude system, where monochromatic flux (in erg/s/cm^2/Hz)
    gives magnitude (Oke, 1974)
                  mag(AB) = -2.5 log(f) - 48.60
    """
    log, log_err = unc.multiply(-2.5, 0, *unc.log10(flux, flux_err))
    return unc.subtract(log, log_err, 48.6, 0)
