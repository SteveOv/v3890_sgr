import os
import pathlib
from pathlib import PurePosixPath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json
from data import FrodoSpecSpectralDataSource as FrodoSpecDS
from data.SpectrumCollectionEx import SpectrumCollectionEx
from specutils import SpectralRegion
# noinspection PyUnresolvedReferences
import plotting
# noinspection PyUnresolvedReferences
import spectrum

from specutils import Spectrum1D

def read_setting(group, name, default=None, printout=True):
    value = group[name] if name in group else default
    if printout:
        print(f"\t{name} = {value}")
    return value


settings = json.load(open("spec_calibration.json"))
for spec_set in ["standard_observation-Hilt102"]: # ["target_observation", "standard_observation-Hilt102"]:
    spec_set_settings = settings["sky_subtraction"][spec_set]
    lambda_h_alpha = read_setting(spec_set_settings, "lambda_line_red", 6563)
    lambda_cont_red = read_setting(spec_set_settings, "lambda_cont_red", 6000)
    lambda_h_beta = read_setting(spec_set_settings, "lambda_line_blue", 4861)
    lambda_cont_blue = read_setting(spec_set_settings, "lambda_cont_blue", 4000)
    lambda_delta = read_setting(spec_set_settings, "lambda_delta", 1000e3)
    plot_nss_spectra = read_setting(spec_set_settings, "plot_nss_spectra", False)

    source_dir = pathlib.Path.home() / read_setting(spec_set_settings, "source_dir", pathlib.Path().cwd())
    output_dir = pathlib.Path.home() / read_setting(spec_set_settings, "output_dir", pathlib.Path().cwd())
    output_dir.mkdir(parents=True, exist_ok=True)

    for fits_group in spec_set_settings["subtraction_settings"]:
        print(f"\n\nProcessing fits group: {fits_group}\n--------------------------------------")
        fits_group_settings = spec_set_settings["subtraction_settings"][fits_group]

        for fits_file_name in spec_set_settings["subtraction_settings"][fits_group]:
            print(f"* Processing {spec_set} / subtraction_settings / {fits_group} / {fits_file_name}")
            fits_settings = fits_group_settings[fits_file_name]

            non_ss_spectra, header = FrodoSpecDS.read_spectra(
                source_dir / fits_file_name, "RSS_NONSS", None, True, fits_file_name)
            is_blue = "blue" in str.lower(header["CONFNAME"])

            # For each NON-SS spectra we calculate the flux ratio between chosen high and low flux regions
            # The two ranges are chosen specifically to discriminate between an object and a "sky" spectrum
            peak_region = spectrum.spectral_region_centred_on(lambda_h_beta if is_blue else lambda_h_alpha, lambda_delta)
            cont_region = spectrum.spectral_region_centred_on(lambda_cont_blue if is_blue else lambda_cont_red, lambda_delta)
            num_spectra = non_ss_spectra.shape[0]
            flux_ratios = np.zeros(num_spectra)
            for spec_ix in np.arange(0, num_spectra):
                # Don't use specutils.extract_spectrum here as it's incredibly slow.
                wl_set = non_ss_spectra.wavelength[spec_ix, :]
                non_ss_spectrum = non_ss_spectra.flux[spec_ix, :]
                h_wavelength_sel = (wl_set >= peak_region.lower) & (wl_set <= peak_region.upper)
                c_wavelength_sel = (wl_set >= cont_region.lower) & (wl_set <= cont_region.upper)
                flux_ratios[spec_ix] = sum(non_ss_spectrum[h_wavelength_sel]) / sum(non_ss_spectrum[c_wavelength_sel])
            min_flux_ratio = min(flux_ratios)
            max_flux_ratio = max(flux_ratios)

            # Plot histogram and heat/fibre map of the ratios.  Also print the standard pipeline ss spectrum for reference.
            # matplotlib.use("Agg")  # Stop annoying popup when debugging plots being saved to file
            plt.rc("font", size=8)
            fig = plt.figure(figsize=(6.4, 9.6), constrained_layout=False)
            gs = GridSpec(ncols=2, nrows=3, width_ratios=[2, 3], height_ratios=[3, 3, 3], wspace=0.4, hspace=0.4, figure=fig)
            fig.suptitle(f"The sky subtraction pipeline of the FRODOSpec asset {fits_file_name}")
            plotting.plot_histogram_to_ax(fig.add_subplot(gs[0, 0]), flux_ratios, is_blue)
            plotting.plot_fibre_heatmap_to_ax(fig, fig.add_subplot(gs[0, 1]), flux_ratios)
            try:
                ss_spec = FrodoSpecDS.read_spectrum(source_dir / fits_file_name, "SPEC_SS")
                plotting.plot_spectrum_to_ax(fig.add_subplot(gs[1, :]), ss_spec, "Standard pipeline sky subtracted spectrum",
                                             cont_region, peak_region)
            except KeyError:
                print("Missing SPEC_SS data")

            # Read in the manual exclusion mask
            man_exclusion_mask = np.ones(144, dtype=bool)
            man_exclusion_mask[read_setting(fits_settings, "excluded_fibres", [])] = False

            #
            # Handle the "sky" fibres - spike detection/exclusion, masking and final selection
            #
            sky_th = read_setting(fits_settings, "sky_th", min_flux_ratio + 3)
            sky_spike_th = read_setting(fits_settings, "sky_spike_th", 100)
            sky_spike_mask = np.ones(num_spectra, dtype=bool)
            for spec_ix in np.arange(0, num_spectra):
                if flux_ratios[spec_ix] <= sky_th \
                        and len(spectrum.detect_spikes(non_ss_spectra[spec_ix, :], sky_spike_th, 0.66, 10)) > 0:
                    sky_spike_mask[spec_ix] = False

            print(f"\tsky_spike_mask = {np.where(sky_spike_mask == False)[0]}")
            sky_mask = (flux_ratios <= sky_th) & (flux_ratios >= 1 / sky_th) & man_exclusion_mask & sky_spike_mask
            sky_spectra = non_ss_spectra.copy_from_spectrum_mask(sky_mask, "sky_spectra")

            #
            # Now we handle the object fibres
            #
            obj_th = read_setting(fits_settings, "obj_th", max([sky_th, 30]))
            obj_spike_removal = read_setting(fits_settings, "spike_removal", None)
            obj_spike_th = read_setting(fits_settings, "obj_spike_th", 100)
            obj_spike_mask = np.ones(num_spectra, dtype=bool)
            for ix in np.arange(0, num_spectra):
                if flux_ratios[ix] >= obj_th:
                    if obj_spike_removal is not None:
                        # We are doing manual spike removal - so no masking
                        if f"{ix}" in obj_spike_removal:
                            spikes_to_remove = spectrum.spectral_regions_from_list(obj_spike_removal[f"{ix}"])
                            if len(spikes_to_remove) > 0:
                                spectrum.remove_spikes(non_ss_spectra[ix], spikes_to_remove)
                    else:
                        # No manual spike removal; auto-spike detection/masking (backwards compatible with existing config)
                        obj_spike_mask[ix] = not (len(spectrum.detect_spikes(non_ss_spectra[ix, :], obj_spike_th)) > 0)
            if obj_spike_removal is None:
                print(f"\tobj_spike_mask = {np.where(obj_spike_mask == False)[0]}")
            obj_mask = (flux_ratios >= obj_th) & man_exclusion_mask & obj_spike_mask
            obj_spectra = non_ss_spectra.copy_from_spectrum_mask(obj_mask, "obj_spectra")

            #
            # Sky subtraction; SS spectra is avg(object) - avg(sky) over all wavelengths (& plot resulting ss_spectrum)
            #
            avg_sky_flux = np.mean(sky_spectra.flux, axis=0)
            avg_obj_flux = np.mean(obj_spectra.flux, axis=0)
            ss_obj_flux = np.subtract(avg_obj_flux, avg_sky_flux)
            ss_spectrum = Spectrum1D(flux=ss_obj_flux, spectral_axis=non_ss_spectra.spectral_axis[0, :])
            plotting.plot_spectrum_to_ax(fig.add_subplot(gs[2, :]), ss_spectrum, "My pipeline sky subtracted spectrum",
                                         sky_flux=avg_sky_flux, c_range=cont_region, h_range=peak_region)
            plt.savefig(output_dir / (fits_file_name + ".png"), dpi=300)
            plt.close()

            # Diagnostics - plot the spectra from every fibre (to a different file to the other plots - it's big!!)
            if plot_nss_spectra:
                plotting.plot_rss_spectra(non_ss_spectra, flux_ratios, fits_file_name,
                                          sky_mask, obj_mask, cont_region, peak_region, output_dir, enhance=False)
