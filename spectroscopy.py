import json
import matplotlib
import matplotlib.pyplot as plt
from data.DataSource import *
from data.CalibratedSpectralDataSource import *
from plot import *

# Placeholder for pulling together all of the spectroscopy tasks

# Test code - will be replaced with a specific data source once spectral pipeline completed.
ds_be = DataSource.create("CalibratedSpectralDataSource",
            "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/flux_cal_pipeline/calibrated/cal_b_e_20190828_3.fits")

ds_re = DataSource.create("CalibratedSpectralDataSource",
            "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/flux_cal_pipeline/calibrated/cal_r_e_20190828_3.fits")

spec_be = ds_be.query()
spec_re = ds_re.query()
header = ds_be.header

fig = plt.figure(figsize=[6.4, 3.2], constrained_layout=True)
ax = fig.add_subplot(1, 1, 1)
ax.set_title(f"The sky-subtracted and flux calibrated spectra at MJD={header['MJD']:.2f} d")
ax.set_xlabel(f"Wavelength [{spec_be.spectral_axis.unit}]")
ax.set_ylabel(f"Arbitrary flux [{spec_be.flux.unit}]")
ax.set_yticks([], minor=False)
ax.set_xticks(np.arange(3500, 8500, 500), minor=False)
ax.set_xticks(np.arange(3500, 8500, 50), minor=True)
ax.plot(spec_be.spectral_axis, spec_be.flux, label=f"blue arm", color="b", linestyle="-", linewidth=0.25)
ax.plot(spec_re.spectral_axis, spec_re.flux, label="red arm", color="r", linestyle="-", linewidth=0.25)
ax.legend(loc="upper left")
plt.show()
plt.close()
