import pathlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import json
from astropy.io import fits
from specutils import SpectrumList

# noinspection PyUnresolvedReferences
import plotting

from data import FrodoSpecSpectralDataSource as FrodoSpecDS
from spectroscopy import SpectrumCollectionEx, Spectrum1DEx


def read_setting(group, name, default=None, printout=True):
    value = group[name] if name in group else default
    if printout:
        print(f"\t{name} = {value}")
    return value


settings = json.load(open("spec_calibration.json"))
for spec_set in ["std-obs-Hilt102-blue", "std-obs-Hilt102-red", "target-obs-blue", "target-obs-red"]:
    spec_set_settings = settings["sky_subtraction"][spec_set]
    lambda_high = read_setting(spec_set_settings, "lambda_high", 6563)
    lambda_low = read_setting(spec_set_settings, "lambda_low", 6000)
    lambda_delta = read_setting(spec_set_settings, "lambda_delta", 1000e3)
    high_region = Spectrum1DEx.spectral_region_centred_on(lambda_high, lambda_delta)
    low_region = Spectrum1DEx.spectral_region_centred_on(lambda_low, lambda_delta)

    plot_rss_spectra = read_setting(spec_set_settings, "plot_rss_spectra", True)
    expand_rss_spectra = read_setting(spec_set_settings, "expand_rss_spectra", False)

    # These are defaults which may be overridden on a fibre by fibre basis.
    def_sky_th = read_setting(spec_set_settings, "sky_th", 3)
    def_sky_spike_th = read_setting(spec_set_settings, "sky_spike_th", 100)
    def_obj_th = read_setting(spec_set_settings, "obj_th", 30)
    def_obj_spike_th = read_setting(spec_set_settings, "obj_spike_th", 100)

    source_dir = pathlib.Path.home() / read_setting(spec_set_settings, "source_dir", pathlib.Path().cwd())
    output_dir = pathlib.Path.home() / read_setting(spec_set_settings, "output_dir", pathlib.Path().cwd())
    output_dir.mkdir(parents=True, exist_ok=True)

    for fits_group in spec_set_settings["subtraction_settings"]:
        print(f"\n\nProcessing fits group: {fits_group}\n--------------------------------------")
        fits_group_settings = spec_set_settings["subtraction_settings"][fits_group]
        fits_group_ss_spectra = SpectrumList()

        # We'll note these are we got through the group as these will form the bases of the output fits.
        source_fits_full_name1 = None
        spec_ss_header = None

        for fits_file_name in spec_set_settings["subtraction_settings"][fits_group]:
            print(f"* Processing {spec_set} / subtraction_settings / {fits_group} / {fits_file_name}")
            fits_settings = fits_group_settings[fits_file_name]

            source_fits_full_name = source_dir / fits_file_name
            non_ss_spectra, hdr = FrodoSpecDS.read_spectra(source_fits_full_name, "RSS_NONSS", None, True, fits_file_name)
            is_blue = "blue" in str.lower(hdr["CONFNAME"])
            if source_fits_full_name1 is None:
                source_fits_full_name1 = source_fits_full_name

            # For each NON-SS spectra we calculate the flux ratio between chosen high and low flux regions
            # The two ranges are chosen specifically to discriminate between an object and a "sky" spectrum
            num_spectra = non_ss_spectra.shape[0]
            flux_ratios = np.zeros(num_spectra)
            for spec_ix in np.arange(0, num_spectra):
                wl_set = non_ss_spectra.wavelength[spec_ix, :]
                non_ss_spectrum = non_ss_spectra.flux[spec_ix, :]
                h_wavelength_sel = (wl_set >= high_region.lower) & (wl_set <= high_region.upper)
                c_wavelength_sel = (wl_set >= low_region.lower) & (wl_set <= low_region.upper)
                flux_ratios[spec_ix] = sum(non_ss_spectrum[h_wavelength_sel]) / sum(non_ss_spectrum[c_wavelength_sel])
            min_flux_ratio = min(flux_ratios)
            max_flux_ratio = max(flux_ratios)

            # Plot histogram and heat/fibre map of ratios.  Also print the standard pipeline ss spectrum for reference.
            # matplotlib.use("Agg")  # Stop annoying popup when debugging plots being saved to file
            plt.rc("font", size=8)
            fig = plt.figure(figsize=(6.4, 9.6), constrained_layout=False)
            gs = GridSpec(ncols=2, nrows=3, width_ratios=[2, 3], height_ratios=[3, 3, 3], wspace=0.4, hspace=0.4, figure=fig)
            fig.suptitle(f"The sky subtraction pipeline of the FRODOSpec asset {fits_file_name}")
            plotting.plot_histogram_to_ax(fig.add_subplot(gs[0, 0]), flux_ratios, is_blue)
            plotting.plot_fibre_heatmap_to_ax(fig, fig.add_subplot(gs[0, 1]), flux_ratios)
            try:
                ss_spec, header = FrodoSpecDS.read_spectrum(source_fits_full_name, "SPEC_SS", header=True)
                plotting.plot_spectrum_to_ax(fig.add_subplot(gs[1, :]), ss_spec,
                                             "Standard pipeline sky subtracted spectrum", low_region, high_region)
                if spec_ss_header is None:
                    spec_ss_header = header
            except KeyError:
                print("Missing SPEC_SS data")

            # Read in the manual exclusion mask
            man_exclusion_mask = np.ones(144, dtype=bool)
            man_exclusion_mask[read_setting(fits_settings, "excluded_fibres", [])] = False

            #
            # Handle the "sky" fibres - spike detection/exclusion, masking and final selection
            #
            sky_th = read_setting(fits_settings, "sky_th", def_sky_th)
            sky_spike_th = read_setting(fits_settings, "sky_spike_th", def_sky_spike_th)
            sky_spike_mask = np.ones(num_spectra, dtype=bool)
            for spec_ix in np.arange(0, num_spectra):
                if flux_ratios[spec_ix] <= sky_th \
                        and len(non_ss_spectra[spec_ix].detect_spikes(sky_spike_th, 0.66, 10)) > 0:
                    sky_spike_mask[spec_ix] = False

            print(f"\tsky_spike_mask = {np.where(sky_spike_mask == False)[0]}")
            sky_mask = (flux_ratios <= sky_th) & (flux_ratios >= 1 / sky_th) & man_exclusion_mask & sky_spike_mask
            sky_spectra = non_ss_spectra.copy_by_spectrum_mask(sky_mask, "sky_spectra")

            #
            # Now we handle the object fibres
            #
            obj_th = read_setting(fits_settings, "obj_th", def_obj_th)
            obj_spike_removal = read_setting(fits_settings, "spike_removal", None)
            obj_spike_th = read_setting(fits_settings, "obj_spike_th", def_obj_spike_th)
            obj_spike_mask = np.ones(num_spectra, dtype=bool)
            for ix in np.arange(0, num_spectra):
                if flux_ratios[ix] >= obj_th:
                    if obj_spike_removal is not None:
                        # We are doing manual spike removal - so no masking
                        if f"{ix}" in obj_spike_removal:
                            spikes_to_remove = Spectrum1DEx.spectral_regions_from_list(obj_spike_removal[f"{ix}"])
                            if len(spikes_to_remove) > 0:
                                non_ss_spectra[ix].remove_spikes(spikes_to_remove)
                    else:
                        # No manual spike removal; spike detection/masking (backwards compatible with existing config)
                        obj_spike_mask[ix] = not (len(non_ss_spectra[ix].detect_spikes(obj_spike_th)) > 0)
            if obj_spike_removal is None:
                print(f"\tobj_spike_mask = {np.where(obj_spike_mask == False)[0]}")
            obj_mask = (flux_ratios >= obj_th) & man_exclusion_mask & obj_spike_mask
            obj_spectra = non_ss_spectra.copy_by_spectrum_mask(obj_mask, "obj_spectra")

            #
            # Sky subtraction; SS spectra is avg(object) - avg(sky) over all wavelengths (& plot resulting ss_spectrum)
            #
            avg_sky_flux = np.mean(sky_spectra.flux, axis=0)
            avg_obj_flux = np.mean(obj_spectra.flux, axis=0)
            ss_obj_flux = np.subtract(avg_obj_flux, avg_sky_flux)
            ss_spectrum = Spectrum1DEx(flux=ss_obj_flux, spectral_axis=non_ss_spectra.spectral_axis[0])
            plotting.plot_spectrum_to_ax(fig.add_subplot(gs[2, :]), ss_spectrum, "My pipeline sky subtracted spectrum",
                                         sky_flux=avg_sky_flux, c_range=low_region, h_range=high_region)
            plt.savefig(output_dir / (fits_file_name + ".png"), dpi=300)
            plt.close()

            # Diagnostics - plot the spectra from every fibre (to a different file to the other plots - it's big!!)
            if plot_rss_spectra:
                plotting.plot_rss_spectra(non_ss_spectra, flux_ratios, fits_file_name,
                                          sky_mask, obj_mask, low_region, high_region, output_dir, expand_rss_spectra)

            fits_group_ss_spectra.append(ss_spectrum)

        # Combine the spectra in the group
        image_file_name = output_dir / f"ss_{fits_group}.png"
        grp_spectra = SpectrumCollectionEx.from_spectra(fits_group_ss_spectra, fits_group)
        grp_spectrum = Spectrum1DEx(flux=np.mean(grp_spectra.flux, axis=0), spectral_axis=grp_spectra.spectral_axis[0])
        plotting.plot_spectrum(grp_spectrum, filename=image_file_name,
                               title=f"My pipeline sky subtracted and combined spectrum for observations {fits_group}")

        # Save to a new fits file
        # Copy the primary HDU from the first file of the set
        data1, header1 = fits.getdata(source_fits_full_name1, hdu=0, header=True)
        prim_hdu = fits.PrimaryHDU(data=data1, header=header1)

        # Now create the HDU for the combined, sky subtracted spectrum - with the header based on that from source fits
        css_hdu = grp_spectrum.create_image_hdu("SPEC_CSS", spec_ss_header)

        hdul = fits.HDUList([prim_hdu, css_hdu])
        hdul.writeto(output_dir / f"ss_{fits_group}.fits", overwrite=True)


