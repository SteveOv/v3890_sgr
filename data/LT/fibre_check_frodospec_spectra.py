import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from data import FrodoSpecSpectralDataSource

lambda_h_alpha = 6563
lambda_h_beta = 4861
d_lambda_h_alpha = (1000e3/2.998e8) * lambda_h_alpha
d_lambda_h_beta = (1000e3/2.998e8) * lambda_h_beta


header, df = FrodoSpecSpectralDataSource.read_spec_into_long_dataframe(
    "/Users/steveo/Documents/V3890_Sgr_Data/LT_Spectra/b_e_20190828_3_1_1_2.fits",
    "RSS_NONSS")

# Which spectrum - it dictates whether we use H-alpha or H-beta as our test wavelength
is_blue = "blue" in header["CONFNAME"]
if is_blue:
    lambda_h = 4861
    lambda_c = 4000
else:
    lambda_h = 6563
    lambda_c = 6000

# Calculate the wavelength ranges
delta_h = (1000e3/2.998e8) * lambda_h
h_range = (lambda_h - delta_h, lambda_h + delta_h)
delta_c = (1000e3/2.998e8) * lambda_c
c_range = (lambda_c - delta_c, lambda_c + delta_c)

mjd = header["MJD"]
date_obs = header["DATE-OBS"]


df_h_line = df.query(f"wavelength >= {h_range[0]} and wavelength <= {h_range[1]}").groupby(["spec"])["flux"].sum()
df_cont = df.query(f"wavelength >= {c_range[0]} and wavelength <= {c_range[1]}").groupby(["spec"])["flux"].sum()
print(df_h_line)

# print a histogram spec numbers along the bottom v flux sums
fig = plt.figure(figsize=(3.2, 3.2), constrained_layout=True)
ax = fig.add_subplot(1, 1, 1)

x = np.arange(0, len(df_h_line))
y = np.divide(df_h_line, df_cont)
#ax.bar(x, y)
n, bins, patches = ax.hist(y)
ax.set_xticks(np.arange(5, 145, 5))
plt.show()
