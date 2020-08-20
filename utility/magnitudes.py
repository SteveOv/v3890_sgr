from typing import Dict, Tuple
from astropy import units as u
from astropy.units import spectral_density, Quantity
from utility import uncertainty_math as unc

# For  converting Vega/J-C magnitudes to to mag(AB)
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
    mag_ab, mag_ab_err = unc.add(mag, mag_err, *mag_ab_correction_factors[band])
    return mag_ab, mag_ab_err


def mag_ab_to_mag_vega(mag_ab, mag_ab_err, band: str = "V"):
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


def mag_ab_to_flux_density_cgs_angstrom(mag_ab, mag_ab_err, band: str = "V"):
    """
    Calculate the flux density, in units erg / s / cm^2 / Angstrom, of the passed mag(AB) value
    """
    flux, err = mag_ab_to_flux_density_jy(mag_ab, mag_ab_err)
    flux_units = units_flux_density_cgs_angstrom
    new_flux = Quantity(flux, u.astrophys.Jy).to(flux_units, equivalencies=spectral_density(lambda_eff[band] * u.AA))
    new_err = Quantity(err, u.astrophys.Jy).to(flux_units, equivalencies=spectral_density(lambda_eff[band] * u.AA))
    return new_flux, new_err


def mag_vega_to_flux_density_cgs_angstrom(mag_vega, mag_vega_err, band: str = "V"):
    """
    Calculate the flux density, in units erg / s / cm^2 / Angstrom, of the passed mag(Vega) value.
    Convenience function which wraps mag_vega_to_mag_ab and mag_ab_to_flux_density_cgs_angstrom
    """
    mag_ab, mag_ab_err = mag_vega_to_mag_ab(mag_vega, mag_vega_err, band=band)
    return mag_ab_to_flux_density_cgs_angstrom(mag_ab, mag_ab_err, band)
