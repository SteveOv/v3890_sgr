import numpy as np


def calc_wavelength_range(lambda_c: float, width_ms: float):
    delta = (width_ms/2.998e8) * lambda_c
    return lambda_c - delta, lambda_c + delta


def detect_spikes(spec_flux, candidate_threshold: float = 100, falloff_fraction: float = 0.75, check_offset: float = 3):
    # Candidates are threshold X mean non_ss_spectra
    candidates = np.where(spec_flux >= (candidate_threshold * np.mean(spec_flux)))[0]
    spikes = []

    mean_flux = np.mean(spec_flux)
    ix_last_flux_to_check = len(spec_flux) - check_offset - 1
    for c_ix in candidates:
        if (c_ix + 1) in candidates:
            # If its neighbour is in the list then it can't be a spike
            pass
        elif check_offset <= c_ix <= ix_last_flux_to_check:
            # A spike must have a precipitous fall in non_ss_spectra either side (be default, losing > 0.75 non_ss_spectra either side)
            previous_flux = spec_flux[c_ix - check_offset]
            next_flux = spec_flux[c_ix + check_offset]
            this_flux = spec_flux[c_ix]
            falloff = this_flux - ((this_flux - mean_flux) * falloff_fraction)
            if falloff > previous_flux and falloff > next_flux:
                spikes.append((c_ix - check_offset, c_ix + check_offset))

    return spikes


def remove_spikes(spec_flux):
    return
