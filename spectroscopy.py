import json
import matplotlib
import matplotlib.pyplot as plt
from data import *
from plot import *

# Placeholder for pulling together all of the spectroscopy tasks

# Test code - will be replaced with a specific data source once spectral pipeline completed.
header, df_be = FrodoSpecSpectralDataSource.read_spec_into_long_dataframe(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/output/00.58_b_e_20190828_3_1_1_2_med_spec_ss.fits",
    "SPEC_SS_MED")

_, df_re = FrodoSpecSpectralDataSource.read_spec_into_long_dataframe(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/output/00.58_r_e_20190828_3_1_1_2_med_spec_ss.fits",
    "SPEC_SS_MED")

fig = plt.figure(figsize=[3.2, 3.2], constrained_layout=True)
ax = fig.add_subplot(1, 1, 1)
ax.set_title(f"The blue and red arm spectra at $\\Delta t={header['DELTA-T']}$ d")
ax.set_xlabel("Wavelength [angstrom]")
ax.set_ylabel("Arbitrary flux")
ax.set_yticks([], minor=False)
ax.set_xticks(np.arange(3500, 8500, 500), minor=False)
ax.set_xticks(np.arange(3500, 8500, 50), minor=True)
ax.plot(df_be["wavelength"], df_be["flux"], label=f"blue arm (gain={header['MED-GAIN']})", color="b", linestyle="-", linewidth=0.25)
ax.plot(df_re["wavelength"], df_re["flux"], label="red arm", color="r", linestyle="-", linewidth=0.25)
ax.legend(loc="upper left")
plt.show()
plt.close()
