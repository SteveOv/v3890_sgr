from typing import Tuple
import numpy as np
from astropy import units
from astropy.units import Quantity
from specutils import SpectralRegion, Spectrum1D


def create_spectral_region(lambda_c: float, width_ms: float) -> SpectralRegion:
    delta = (width_ms/2.998e8) * lambda_c
    region = SpectralRegion(units.Quantity(lambda_c - delta, "Angstrom"), units.Quantity(lambda_c + delta, "Angstrom"))
    return region


def detect_spikes(spectrum: Spectrum1D, candidate_threshold: float = 100,
                  falloff_fraction: float = 0.75, check_offset: float = 3):

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
            # A spike must have a precipitous fall in non_ss_spectra either side (be default, losing > 0.75 non_ss_spectra either side)
            previous_flux = spectrum.flux[c_ix - check_offset]
            next_flux = spectrum.flux[c_ix + check_offset]
            this_flux = spectrum.flux[c_ix]
            falloff = this_flux - ((this_flux - mean_flux) * falloff_fraction)
            if falloff > previous_flux and falloff > next_flux:
                spikes.append((c_ix - check_offset, c_ix + check_offset))

    return spikes


def remove_spikes(spec_flux):
    return
