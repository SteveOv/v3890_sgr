import json
import matplotlib
import matplotlib.pyplot as plt
from data.FrodoSpecSpectralDataSource import *
from plot import *

# Placeholder for pulling together all of the spectroscopy tasks

# Test code - will be replaced with a specific data source once spectral pipeline completed.
spec_be, header = FrodoSpecSpectralDataSource.read_spectrum(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/JL19A06private2105703012reduced/SPEC_SS_extract/03.66_b_e_20190831_11_1_1_2_med_spec_ss.fits",
    "SPEC_SS_MED", header=True)

spec_re = FrodoSpecSpectralDataSource.read_spectrum(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/JL19A06private2105703012reduced/SPEC_SS_extract/03.66_r_e_20190831_11_1_1_2_med_spec_ss.fits",
    "SPEC_SS_MED")

fig = plt.figure(figsize=[6.4, 3.2], constrained_layout=True)
ax = fig.add_subplot(1, 1, 1)
ax.set_title(f"The blue and red arm spectra at $\\Delta t={header['DELTA-T']}$ d")
ax.set_xlabel(f"Wavelength [{spec_be.spectral_axis.unit}]")
ax.set_ylabel(f"Arbitrary flux [{spec_be.flux.unit}]")
ax.set_yticks([], minor=False)
ax.set_xticks(np.arange(3500, 8500, 500), minor=False)
ax.set_xticks(np.arange(3500, 8500, 50), minor=True)
ax.plot(spec_be.spectral_axis, spec_be.flux, label=f"blue arm (gain={header['MED-GAIN']})", color="b", linestyle="-", linewidth=0.25)
ax.plot(spec_re.spectral_axis, spec_re.flux, label="red arm", color="r", linestyle="-", linewidth=0.25)
ax.legend(loc="upper left")
plt.show()
plt.close()
