import pathlib
from astropy.io import fits
from data import FrodoSpecSpectralDataSource as FrodoSpecDS


source_dir = "Documents/V3890_Sgr_Data/LT_Spectra/JL19A06private2105703012reduced/"
output_dir = "Documents/V3890_Sgr_Data/LT_Spectra/fs_resolving_power"
sources = {
    "r_e_20190828_3_1_1_2": [3, 25],
    "r_e_20190828_3_2_1_2": [46],
    "r_e_20190828_3_3_1_2": [11, 81, 143],
    "r_e_20190828_11_1_1_2": [24],
    "r_e_20190828_11_2_1_2": [108],
    "r_e_20190828_11_3_1_2": [14, 51, 143]
}


for source_key, spec_ixs in sources.items():
    source_fits_full_name = pathlib.Path.home() / source_dir / f"{source_key}.fits.gz"

    # Get all the rss spectra
    non_ss_spectra, hdr = FrodoSpecDS.read_spectra(source_fits_full_name, "RSS_NONSS", None, True, source_key)
    for spec_ix in spec_ixs:
        # Extract the required spectrum
        non_ss_spectrum = non_ss_spectra[spec_ix]

        # Copy over the primary HDU
        data1, header1 = fits.getdata(source_fits_full_name, hdu=0, header=True)
        prim_hdu = fits.PrimaryHDU(data=data1, header=header1)

        # Use the RSS_NONSS headers for this spectrum as they will have the appropriate axes set up
        non_ss_hdu = non_ss_spectrum.create_image_hdu("SPEC_NON_SS", hdr)

        output_file = pathlib.Path.home() / output_dir / f"{source_key}_{spec_ix}.fits"
        hdul = fits.HDUList([prim_hdu, non_ss_hdu])
        hdul.writeto(output_file, overwrite=True)
