from typing import Dict, Tuple, Union
from astropy import units as u
from astropy.units import spectral_density, Quantity
from utility import uncertainty_math as unc

# For converting Vega/J-C magnitudes: mag(AB) - Vega mag = factor
mag_ab_correction_factors = {
    # FROM https://www.cfa.harvard.edu/~dfabricant/huchra/ay145/mags.html TODO: get a formal reference for these
    "B": (-0.163, 0.004),
    "V": (-0.044, 0.004),
    "R": (0.055, 0.0),
    "I": (0.309, 0.0),

    # From Breeveld (2010) Swift-UVOT-CALDDB-16-R01
    "UVM2": (1.69, 0.0),
    "UVW2": (1.73, 0.0)
}

# The effective wavelength of each bandpass, in Angstrom
lambda_eff = {
    # UVM2, UVW2 values from Breeveld (2010) Swift-UVOT-CALDDB-16-R01
    "UVM2": 1991,
    "UVW2": 2221,

    # Standard Johnson-Cousins values
    "B": 4353,
    "V": 5477,
    "R": 6349,
    "I": 8797
}

units_flux_density_cgs_angstrom = u.erg / u.cgs.cm**2 / u.s / u.AA


def mag_vega_to_mag_ab(mag, mag_err, band: str = "V"):
    # If mag(AB) - V_mag = corr --> mag(AB) = corr + V_mag
    mag_ab, mag_ab_err = unc.add(mag, mag_err, *mag_ab_correction_factors[band])
    return mag_ab, mag_ab_err


def mag_ab_to_mag_vega(mag_ab, mag_ab_err, band: str = "V"):
    # If mag(AB) - V_mag = corr --> -V_mag = corr - mag(AB) --> V_mag = mag(AB) - corr
    mag_vega, mage_vega_err = unc.subtract(mag_ab, mag_ab_err, *mag_ab_correction_factors[band])
    return mag_vega, mage_vega_err


def mag_ab_to_flux_density_jy(mag_ab, mag_ab_err=0):
    """
    Calculate the flux, in units of Jansky, of the passed mag(AB)

    Based on the standard definition of the magnitude system, where monochromatic flux (in erg/s/cm^2/Hz)
                  f = 10^( -0.4( mag(AB) + 48.60 ) )
    if you work through that 1 Jy = 10^-23, so f [Jy] = f/10^-23, you get
                  f = 10^( 0.4( 8.9 - mag(AB) ) ) Jy
    """
    exponent, exponent_err = unc.multiply(0.4, 0, *unc.subtract(8.9, 0, mag_ab, mag_ab_err))
    return unc.power(10, 0, exponent, exponent_err)


def mag_ab_to_flux_density_cgs_hz(mag_ab, mag_ab_err=0):
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


def flux_density_cgs_hz_to_mag_ab(flux, flux_err):
    """
    Calculate the flux, in units of erg/s/cm^2/Hz, of the passed mag(AB) value.

    Based on the standard definition of the magnitude system, where monochromatic flux (in erg/s/cm^2/Hz)
    gives magnitude (Oke, 1974)
                  mag(AB) = -2.5 log(f) - 48.60
    """
    log, log_err = unc.multiply(-2.5, 0, *unc.log10(flux, flux_err))
    return unc.subtract(log, log_err, 48.6, 0)


def flux_density_jy_to_cgs_angstrom(flux: Union[float, Quantity], flux_err: Union[float, Quantity], band: str = "V") \
        -> Tuple[Quantity, Quantity]:
    """
    Convert a flux density from units of Jansky to units erg / s / cm^2 / Angstrom.
    """
    flux_jy = flux if isinstance(flux, Quantity) else flux * u.astrophys.Jy
    flux_err_jy = flux_err if isinstance(flux_err, Quantity) else flux_err * u.astrophys.Jy

    flux_units = units_flux_density_cgs_angstrom
    lambda_eff_angstrom = lambda_eff[band] * u.AA

    flux_cgs = flux_jy.to(flux_units, equivalencies=spectral_density(lambda_eff_angstrom))
    flux_cgs_err = flux_err_jy.to(flux_units, equivalencies=spectral_density(lambda_eff_angstrom))
    return flux_cgs, flux_cgs_err


def E_gr_to_E_BV(egr: float, egr_err: float) -> Tuple[float, float]:
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
    # B-V = 0.3130(g-r) - 0.2271 + 0.5784(g-r) + 0.0038
    # d(B-V) = sqrt(0.0107^2 + 0.0054^2)
    #
    B_V, B_V_err = unc.subtract(*unc.multiply(0.8914, 0, egr, egr_err), 0.2233, 0)
    B_V_err = unc.uncertainty_add_or_subtract(B_V_err, 0.0119854)
    return B_V, B_V_err

