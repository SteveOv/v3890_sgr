import json
from data.CalibratedSpectralDataSource import *
from plot import *

# Placeholder for pulling together all of the spectroscopy tasks

# Test code - will be replaced with a specific data source once spectral pipeline completed.
ds_be = DataSource.create(
    "CalibratedSpectralDataSource",
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/flux_cal_pipeline/calibrated/cal_b_e_20190828_3.fits")

ds_re = DataSource.create(
    "CalibratedSpectralDataSource",
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/flux_cal_pipeline/calibrated/cal_r_e_20190828_3.fits")

spec_be = ds_be.query()
spec_re = ds_re.query()
header = ds_be.header

plot_config = {
    "type": "SpectrumPlot",
    "file_name": "./output/test_spectrum.png",
    "title": f"The sky-subtracted and flux calibrated spectra at MJD={header['MJD']:.2f} d",
    "params": {
    }
}

PlotHelper.plot_to_file(plot_config, spectra=[spec_be, spec_re])

