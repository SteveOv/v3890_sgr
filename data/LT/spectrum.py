from typing import List
import warnings
import numpy as np
from astropy.units import Quantity
from astropy.utils.exceptions import AstropyUserWarning
from specutils import SpectralRegion, Spectrum1D


def spectral_region_centred_on(lambda_c: float, width_ms: float, units: str = "Angstrom") -> SpectralRegion:
    delta = (width_ms/2.998e8) * lambda_c
    region = SpectralRegion(Quantity(lambda_c - delta, units), Quantity(lambda_c + delta, units))
    return region


def spectral_region_over(lambda_from: float, lambda_to: float, units: str = "Angstrom") -> SpectralRegion:
    region = SpectralRegion(Quantity(lambda_from, units), Quantity(lambda_to, units))
    return region


def spectral_regions_from_list(lambda_list: List[List[float]], units: str = "Angstrom") -> List[SpectralRegion]:
    region_list = []
    for item in lambda_list:
        if len(item) == 2:
            region_list.append(spectral_region_over(min(item), max(item), units))
    return region_list


def detect_spikes(spectrum: Spectrum1D, candidate_threshold: float = 100,
                  falloff_fraction: float = 0.75, check_offset: float = 3) -> List[SpectralRegion]:

    # Candidates are threshold X mean non_ss_spectra
    mean_flux = np.mean(spectrum.flux)
    flux_threshold = candidate_threshold * mean_flux    # candidate_threshold must not have units otherwise we get adu2
    candidates = np.where(spectrum.flux >= flux_threshold)[0]
    spikes = []

    ix_last_flux_to_check = len(spectrum.flux) - check_offset - 1
    for c_ix in candidates:
        if (c_ix + 1) in candidates:
            # If its neighbour is in the list then it can't be a spike
            pass
        elif check_offset <= c_ix <= ix_last_flux_to_check:
            # A spike must have a precipitous fall in non_ss_spectra either side
            # (by default, losing > 0.75 non_ss_spectra either side)
            previous_flux = spectrum.flux[c_ix - check_offset]
            next_flux = spectrum.flux[c_ix + check_offset]
            this_flux = spectrum.flux[c_ix]
            falloff = this_flux - ((this_flux - mean_flux) * falloff_fraction)
            if falloff > previous_flux and falloff > next_flux:
                lambda_from = spectrum.wavelength[c_ix - check_offset]
                lambda_to = spectrum.wavelength[c_ix + check_offset]
                spikes.append(
                    SpectralRegion(lambda_from, lambda_to))

    return spikes


def remove_spikes(spectrum: Spectrum1D, spikes: List[SpectralRegion]):
    for spike in spikes:
        _linear_interpolation_exciser(spectrum, spike)
    return


def _linear_interpolation_exciser(spectrum: Spectrum1D, region: SpectralRegion):
    """
    This is a copy of the specutils' linear_exciser function with bug fixes so that it actually works.
    """
    # Don't take copies - we're going to do this in place
    spectral_axis = spectrum.spectral_axis
    flux = spectrum.flux
    if spectrum.uncertainty is not None:
        new_uncertainty = spectrum.uncertainty
    else:
        new_uncertainty = None

    # Need to add a check that the subregions don't overlap, since that could
    # cause undesired results. For now warn if there is more than one subregion
    if len(region) > 1:
        # Raise a warning if the SpectralRegion has more than one subregion, since
        # the handling for this is perhaps unexpected
        warnings.warn("A SpectralRegion with multiple subregions was provided as "
             "input. This may lead to undesired behavior with linear_exciser if "
             "the subregions overlap.",
             AstropyUserWarning)

    for subregion in region:
        # Find the indices of the spectral_axis array corresponding to the subregion
        region_mask = (spectral_axis >= subregion.lower) & (spectral_axis < subregion.upper)
        inclusive_indices = np.nonzero(region_mask)[0]

        # Now set the flux values for these indices to be a linear range
        s, e = max(inclusive_indices[0]-1, 0), min(inclusive_indices[-1]+1, spectral_axis.size-1)

        # Fixed the bug here, where the specutils code's call to linspace generates Quantity with underlying value array
        # of float64, which when written to the modified_flux Quantity (float32) causes a loss of precision error!!!
        # new_flux = np.linspace(flux[s], flux[e], modified_flux[s: e + 1].size)
        new_flux = np.linspace(flux[s].value, flux[e].value, flux[s:e+1].size, dtype=flux.dtype.type)
        old_flux = flux[s:e+1]
        print(f"\tLinear interpolation of ({subregion.lower}, {subregion.upper}); replacing {old_flux} with {new_flux}")
        flux[s:e+1] = Quantity(new_flux, flux.unit)

        # Add the uncertainty of the two linear interpolation endpoints in
        # quadrature and apply to the excised region.
        if new_uncertainty is not None:
            new_uncertainty[s:e] = np.sqrt(spectrum.uncertainty[s]**2 + spectrum.uncertainty[e]**2)
    return
