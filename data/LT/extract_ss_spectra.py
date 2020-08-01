import glob
import os
import warnings
import numpy as np
from astropy.io import fits

eruption_jd = 2458723.278
delta_t_offset = np.subtract(2400000, eruption_jd)
blue_gain = 10  # The amount of gain to apply to blue combined spectra

# V3890 Sgr assets
source_path = "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/JL19A06private2105703012reduced"
output_path = f"{source_path}/SPEC_SS_extract/"

# Standard/calibration spectra
# source_path = "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/standard-observations/**"
# output_path = "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/standard-observations/SPEC_SS_extract/"


fits_1 = sorted(glob.glob(F"{source_path}/?_e_????????_*_1_?_2.fits*", recursive=True), key=os.path.basename)
fits_2 = sorted(glob.glob(F"{source_path}/?_e_????????_*_2_?_2.fits*", recursive=True), key=os.path.basename)
fits_3 = sorted(glob.glob(F"{source_path}/?_e_????????_*_3_?_2.fits*", recursive=True), key=os.path.basename)


for ix in np.arange(0, len(fits_1)):
    is_blue = []
    median_hdr = None
    source_data = []
    mjd = [] * 3
    conf_name = [] * 3
    delta_t = [] * 3
    exp_ix = 0

    print("\n-------------------------------------------------------")
    ffs = [fits_1[ix]]
    if len(fits_2) >= ix+1: ffs.append(fits_2[ix])
    if len(fits_3) >= ix+1: ffs.append(fits_3[ix])
    for fits_file in ffs:
        print(f"From Input file:\t\t{fits_file}")
        id_string = F"'{os.path.basename(fits_file)}"

        # read the SPEC_SS HDU from  source file - this contains the Sky subtracted spectrum we need
        data, hdr = fits.getdata(fits_file, "SPEC_SS", header=True)

        # Some validation
        exp_total = hdr["EXPTOTAL"] if "EXPTOTAL" in hdr else "<missing>"
        if exp_total != 3:
            warnings.warn(F"{id_string}: Expected EXPTOTAL==3, actually=={exp_total}")
        exp_num = hdr["EXPNUM"] if "EXPNUM" in hdr else "<missing>"
        if exp_num != exp_ix + 1:
            warnings.warn(F"{id_string}: Expected EXPNUM=={exp_ix + 1}, actually=={exp_num}")
        cat_name = hdr["CAT-NAME"] if "CAT-NAME" in hdr else "<missing>"
        if cat_name != "V3890_Sgr":
            warnings.warn(F"{id_string}: Expected CAT-NAME=='V3890_Sgr', actually=='{cat_name}'")

        # We need to work out the epoch of this spectrum, relative to the eruption time.
        temp_mjd = hdr["MJD"] if "MJD" in hdr else None
        if temp_mjd is None:
            warnings.warn(f"{id_string}: Expected to find an MJD header but none present")
        else:
            mjd.append(temp_mjd)
            delta_t.append(np.add(temp_mjd, delta_t_offset))

        # Need to know whether this is a blue spectrum as we will apply gain to better match it with red spectra
        temp_conf_name = hdr["CONFNAME"] if "CONFNAME" in hdr else ""
        is_blue.append(temp_conf_name == "FRODO-blue-high")
        conf_name.append(temp_conf_name)

        # Take a copy of the data and keep the first exposure's headers for use with the combined spectrum
        if data is not None and data.size > 1:
            source_data.append(data)
        if exp_ix == 0:
            median_hdr = hdr
            median_hdr["DELTA-T"] = f"{delta_t[exp_ix]:.4f}"
        exp_ix += 1

    # We should now have the three sets of data.  We work out a fourth set with the median value as the data.
    median_data = []
    if not (sd.size == source_data[0].size for sd in source_data):
        warnings.warn("Source data of different size - cannot take median")
    if not (is_it for is_it in is_blue):
        warnings.warn("Not all selected spectrum were of the same type - cannot take median")
    else:
        if len(source_data) != 3:
            warnings.warn(f"Expected 3 spectra, but only {len(source_data)} could be retrieved.  Median based on this")

        # Generate the median output, and if a blue arm spectrum apply the required amount of gain
        median_data = np.median(source_data, axis=0)
        median_hdr["MED-OF"] = len(source_data)
        if is_blue[0]:
            median_data = np.multiply(median_data, blue_gain)
            median_hdr["MED-GAIN"] = blue_gain
        else:
            median_hdr["MED-GAIN"] = 0

    # Generate the name of the common output fits file.
    m_delta_t = np.mean(delta_t)
    output_fits = f"{m_delta_t:05.2f}_{os.path.splitext(os.path.splitext(os.path.basename(fits_1[ix]))[0])[0]}_med_spec_ss.fits"
    output_fits = os.path.join(output_path, output_fits)
    print(f"Preparing Output file:\t{output_fits}\n\t<MJD> = {np.mean(mjd):.3f}, <Delta-T> = {m_delta_t:.2f}, CONFNAME={conf_name}")
    if os.path.exists(output_fits):
        os.remove(output_fits)

    # Copy the PrimaryHDU from the "1" file to the output file
    # we're not bothered with the image data but it's not valid without it
    primary_data, primary_hdr = fits.getdata(fits_1[ix], "L1_IMAGE", header=True)
    fits.writeto(output_fits, primary_data, primary_hdr)

    # Create as much of the output as possible
    median_hdr["EXPNUM"] = 0
    median_hdr["EXTNAME"] = "SPEC_SS_MED"
    fits.append(output_fits, median_data, median_hdr)
