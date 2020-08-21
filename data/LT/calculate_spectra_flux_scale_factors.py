import json
import pandas as pd
from fitting import *
import spectra_lookup
from astropy import units as u
from utility import magnitudes as mag, uncertainty_math as umath

settings = json.load(open("../../photometry.json"))

# The way the config is set up the lightcurves/fit_sets have the same keys
fit_set_group_config = settings["fit_set_groups"]["V3890-Sgr-2019-Vis-nominal"]
lightcurve_group_config = settings["lightcurve_groups"][fit_set_group_config["lightcurve_group"]]
data_source_config = settings["data_sources"][lightcurve_group_config["data_source"]]
data_source_config["file_spec"] = "../../" + data_source_config["file_spec"]

ds = DataSource.create_from_config(data_source_config)
lightcurves = {}
for lc_key, lc_config in lightcurve_group_config["lightcurves"].items():
    lightcurves[lc_key] = Lightcurve.create_from_data_source(lc_key, ds, lightcurve_group_config)

fit_sets = {}
fit_set_type = fit_set_group_config["type"] if "type" in fit_set_group_config else "StraightLineLogXFitSet"
for fs_key, fs_config in fit_set_group_config["fit_sets"].items():
    lightcurve = lightcurves[fs_key]
    fit_sets[fs_key] = \
        StraightLineLogXFitSet.fit_to_data(fs_key, lightcurve, "day", "mag", "mag_err", fs_config['breaks'])

# Get the timing of the spectra wrt the photometry
eruption_jd = lightcurve_group_config["eruption_jd"]
epochs = spectra_lookup.get_spectra_epochs(eruption_jd)

# Read in the output values from IRAF onedspec sbands operation.
df = pd.read_csv("./sbands_fluxes.txt", skiprows=np.arange(0, 11), header=None, index_col=None, delim_whitespace=True)
df.columns = ["fits", "band", "flux"]

print(f"\nThe spectra scale factors")
for spec_key, delta_t in epochs.items():
    band = str.upper(spec_key[0])

    # Use the photometric fit to get the Vega mag in the appropriate band, then convert it
    # to mag(AB) and then a flux [erg/s/cm^2/Angstrom] (the same units as the flux from sbands).
    vega_mag = fit_sets[f"{band}-band"].find_y_value(delta_t)
    mag_ab, mag_ab_err = mag.mag_vega_to_mag_ab(vega_mag.nominal_value, vega_mag.std_dev, band)
    flux_jy, flux_jy_err = mag.mag_ab_to_flux_density_jy(mag_ab, mag_ab_err)
    flux_cgs, flux_cgs_err = mag.flux_density_jy_to_cgs_angstrom(flux_jy, flux_jy_err, band)

    # The scale_factor is the ratio of the photometric flux to the sbands flux taken from the spectrum
    sbands_flux = df.query(f"fits.str.contains('{spec_key}') and band=='{band}'", engine="python")["flux"].values[0]
    sbands_flux_cgs = sbands_flux * mag.units_flux_density_cgs_angstrom
    scale_factor, scale_factor_err = umath.divide(flux_cgs, flux_cgs_err, sbands_flux_cgs, 0)

    # Write out IRAF imarith commands to perform the required scaling.  These can be pasted into the IRAF command line.
    print(f"imarith ./calibrated/cal_{spec_key}.fits * {scale_factor} ./scaled/scaled_{spec_key}.fits")


