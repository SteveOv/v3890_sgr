import glob
import os
from astropy.io import fits


fits_file_names = glob.glob(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/JL19A06private2105703012reduced/b_e_20190828_3_1_1_2.fits.gz")
for fits_file_name in sorted(fits_file_names):
    with fits.open(fits_file_name) as hdul:
        print(F"\n\nFor source: {os.path.basename(fits_file_name)}")
        print(F"-------------------------------------------------")
        print(hdul.info())

        for hdu in hdul:
            print(F"\n\nFor HDU: {hdu.name}\n-------------------------------")
            for key in hdu.header:
                print(F"HDU['{hdu.name}'].header['{key}'] = '{hdu.header[key]}'")
