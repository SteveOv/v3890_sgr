import os
import pathlib
from pathlib import PurePosixPath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json
from data import FrodoSpecSpectralDataSource as FrodoSpecDS
# noinspection PyUnresolvedReferences
import plotting
# noinspection PyUnresolvedReferences
import spectrum
from astropy import units

from specutils import Spectrum1D, SpectrumCollection
from specutils.manipulation import extract_region

def read_setting(group, name, default=None):
    return group[name] if name in group else default


settings = json.load(open("spec_calibration.json"))
for spec_group in ["target_observation", "standard_observation"]:
    group_settings = settings["sky_subtraction"][spec_group]
    lambda_h_alpha = read_setting(group_settings, "lambda_line_red", 6563)
    lambda_cont_red = read_setting(group_settings, "lambda_cont_red", 6000)
    lambda_h_beta = read_setting(group_settings, "lambda_line_blue", 4861)
    lambda_cont_blue = read_setting(group_settings, "lambda_cont_blue", 4000)
    lambda_delta = read_setting(group_settings, "lambda_delta", 1000e3)
    output_dir = pathlib.Path.home() / read_setting(group_settings, "output_dir", pathlib.Path().cwd())
    output_dir.mkdir(parents=True, exist_ok=True)
    for fits_file_name in sorted(pathlib.Path.home().glob(read_setting(group_settings, "source_files", "")), key=os.path.basename):
        print(f"\nProcessing {spec_group.replace('_', ' ')}: {fits_file_name}")

        # Some metadata about the spectral data
        basename = PurePosixPath(fits_file_name.stem).stem
        sub_settings = group_settings["subtraction_settings"][basename]

        non_ss_spectra, header = FrodoSpecDS.read_spectra(fits_file_name, "RSS_NONSS", header=True)
        is_blue = "blue" in str.lower(header["CONFNAME"])

        # For each NON-SS spectra we calculate the flux ratio between chosen high and low flux regions
        # The two ranges are chosen specifically to discriminate between an object and a "sky" spectrum
        peak_region = spectrum.create_spectral_region(lambda_h_beta if is_blue else lambda_h_alpha, lambda_delta)
        cont_region = spectrum.create_spectral_region(lambda_cont_blue if is_blue else lambda_cont_red, lambda_delta)
        num_spectra = non_ss_spectra.shape[0]
        flux_ratios = np.zeros(num_spectra)
        for spec_ix in np.arange(0, num_spectra):
            # Don't use specutils.extract_spectrum here as it's incredibly slow.
            wl_set = non_ss_spectra.wavelength[spec_ix, :]
            non_ss_spectrum = non_ss_spectra.flux[spec_ix, :]
            h_wavelength_sel = (wl_set >= peak_region.lower) & (wl_set <= peak_region.upper)
            c_wavelength_sel = (wl_set >= cont_region.lower) & (wl_set <= cont_region.upper)
            flux_ratios[spec_ix] = sum(non_ss_spectrum[h_wavelength_sel]) / sum(non_ss_spectrum[c_wavelength_sel])

        # Plot histogram and heat/fibre map of the ratios.  Also print the standard pipeline ss spectrum for reference.
        # matplotlib.use("Agg")  # Stop annoying popup when debugging plots being saved to file
        plt.rc("font", size=8)
        fig = plt.figure(figsize=(6.4, 9.6), constrained_layout=False)
        gs = GridSpec(ncols=2, nrows=3, width_ratios=[2, 3], height_ratios=[3, 3, 3], wspace=0.4, hspace=0.4, figure=fig)
        fig.suptitle(f"The sky subtraction pipeline of the FRODOSpec asset {basename}")
        plotting.plot_histogram_to_ax(fig.add_subplot(gs[0, 0]), flux_ratios, is_blue)
        plotting.plot_fibre_heatmap_to_ax(fig, fig.add_subplot(gs[0, 1]), flux_ratios)
        try:
            ss_spec = FrodoSpecDS.read_spectrum(str(fits_file_name), "SPEC_SS")
            plotting.plot_spectrum_to_ax(fig.add_subplot(gs[1, :]), ss_spec, "Standard pipeline sky subtracted spectrum",
                                         cont_region, peak_region)
        except KeyError:
            print("Missing SPEC_SS data")

        # Object and Sky detection settings; the flux ratios (beyond) which we categorise as a sky or object spectrum
        min_flux_ratio = min(flux_ratios)
        max_flux_ratio = max(flux_ratios)
        sky_th = read_setting(sub_settings, "sky_th", min_flux_ratio + 3)
        obj_th = read_setting(sub_settings, "obj_th", max([sky_th, 30]))
        print(f"\tmin(ratio)={min_flux_ratio}, max(ratio)={max_flux_ratio}\n\tsky_th={sky_th}, obj_th={obj_th}")

        # Spike detection - exclude spectra where individual non_ss_spectra readings are greatly in excess of the mean
        sky_spec_spike_mask = np.ones(144, dtype=bool)
        obj_spec_spike_mask = np.ones(144, dtype=bool)
        sky_spike_th = read_setting(sub_settings, "sky_spike_th", 100)
        obj_spike_th = read_setting(sub_settings, "obj_spike_th", 100)
        for spec_ix in np.arange(0, num_spectra):
            non_ss_spectrum = non_ss_spectra[spec_ix, :]
            if flux_ratios[spec_ix] <= sky_th and len(spectrum.detect_spikes(non_ss_spectrum, sky_spike_th, 0.66, 10)) > 0:
                sky_spec_spike_mask[spec_ix] = False
            elif flux_ratios[spec_ix] >= obj_th and len(spectrum.detect_spikes(non_ss_spectrum, obj_spike_th)) > 0:
                obj_spec_spike_mask[spec_ix] = False
        print(f"\tsky_spike_mask(th={sky_spike_th:00.2f})={np.where(sky_spec_spike_mask == False)[0]}")
        print(f"\tobj_spike_mask(th={obj_spike_th:00.2f})={np.where(obj_spec_spike_mask == False)[0]}")

        # ration tooF low & manually exclusion mask
        excluded_fibres = read_setting(sub_settings, "excluded_fibres", [])
        man_exclusion_mask = np.ones(144, dtype=bool)
        man_exclusion_mask[excluded_fibres] = False
        print(f"\tman_exclusion_mask={excluded_fibres}")

        # Selecting which obj_fluxes to average for the object and sky spectra (referring to the exclusion masks)
        sky_spec_mask = (flux_ratios <= sky_th) & (flux_ratios >= 1 / sky_th)
        sky_spec_mask = man_exclusion_mask & sky_spec_spike_mask & sky_spec_mask
        obj_spec_mask = man_exclusion_mask & obj_spec_spike_mask & (flux_ratios >= obj_th)
        print(F"\tsky fibres({np.count_nonzero(sky_spec_mask)})={np.where(sky_spec_mask == True)[0]}")
        print(F"\tobj fibres({np.count_nonzero(obj_spec_mask)})={np.where(obj_spec_mask == True)[0]}")
        sky_fluxes = non_ss_spectra.flux[sky_spec_mask]
        obj_fluxes = non_ss_spectra.flux[obj_spec_mask]

        # TODO: spike removal - will potentially replace spike detection for at least the object spectrum

        # Sky subtraction; SS spectra is avg(object) - avg(sky) over all wavelengths
        avg_sky_flux = np.mean(sky_fluxes, axis=0)
        avg_obj_flux = np.mean(obj_fluxes, axis=0)
        ss_obj_flux = np.subtract(avg_obj_flux, avg_sky_flux)
        ss_spectrum = Spectrum1D(flux=ss_obj_flux, spectral_axis=non_ss_spectra.spectral_axis[0, :])

        # Plot the resulting Sky Subtracted spectrum out to the same figure as the existing plots
        plotting.plot_spectrum_to_ax(fig.add_subplot(gs[2, :]), ss_spectrum, "My pipeline sky subtracted spectrum",
                                     sky_flux=avg_sky_flux, c_range=cont_region, h_range=peak_region)

        plt.savefig(output_dir / (basename + ".png"), dpi=300)
        plt.close()

        # Diagnostics - plot the spectra from every fibre (to a different file to the other plots - it's big!!)
        plotting.plot_rss_spectra(non_ss_spectra, flux_ratios, basename, sky_spec_mask, obj_spec_mask, cont_region, peak_region, output_dir, enhance=False)
