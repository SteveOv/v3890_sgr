import json
from fitting import *
import spectra_lookup
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

# These are the output values copied from IRAF onedspec sbands operation.
sbands_fluxes = {
    "b_e_20190828_3": 6.34790E-13,
    "b_e_20190828_11": 9.67548E-13,
    "b_e_20190830_5": 6.27379E-13,
    "b_e_20190831_5": 3.57901E-13,
    "b_e_20190831_11": 3.15411E-13,
    "b_e_20190901_5": 3.34849E-13,
    "b_e_20190901_11": 1.89696E-13,
    "b_e_20190902_5": 3.41798E-13,
    "b_e_20190902_7": 2.84326E-13,
    "b_e_20190903_5": 2.86212E-13,
    "b_e_20190903_7": 2.48210E-13,
    "b_e_20190904_4": 2.93339E-13,
    "b_e_20190905_5": 2.51051E-13,
    "b_e_20190905_7": 1.21134E-13,
    "b_e_20190910_1": 1.68551E-13,
    "b_e_20190911_5": 1.14096E-13,
    "b_e_20190911_7": 5.97705E-14,
    "b_e_20190913_5": 1.45967E-14,
    "b_e_20190913_7": 3.45840E-14,
    "b_e_20190915_5": 4.67948E-14,
    "r_e_20190828_3": 2.04257E-12,
    "r_e_20190828_11": 2.07057E-12,
    "r_e_20190830_5": 1.01868E-12,
    "r_e_20190831_5": 6.95945E-13,
    "r_e_20190831_11": 6.22397E-13,
    "r_e_20190901_5": 8.50185E-13,
    "r_e_20190901_11": 8.52628E-13,
    "r_e_20190902_5": 6.64032E-13,
    "r_e_20190902_7": 6.71659E-13,
    "r_e_20190903_5": 5.54302E-13,
    "r_e_20190903_7": 3.85550E-13,
    "r_e_20190904_4": 4.06901E-13,
    "r_e_20190905_5": 3.41113E-13,
    "r_e_20190905_7": 2.33229E-13,
    "r_e_20190910_1": 1.76158E-13,
    "r_e_20190911_5": 1.38241E-13,
    "r_e_20190911_7": 1.06742E-13,
    "r_e_20190913_5": 3.48328E-14,
    "r_e_20190913_7": 7.25394E-14,
    "r_e_20190915_5": 8.65306E-14
}

print(f"\nThe spectra scale factors")
for spec_key, delta_t in epochs.items():
    band = str.upper(spec_key[0])

    # Use the fit_set to get the Vega mag, then convert to mag(AB) and then a flux [erg/s/cm^2/Hz]
    vega_mag = fit_sets[f"{band}-band"].find_y_value(delta_t)
    flux, flux_err = \
        mag.flux_density_jy_from_mag_ab(*mag.mag_ab_from_mag_vega(vega_mag.nominal_value, vega_mag.std_dev, band))
    # print(f"{spec_key}: flux = {flux} +/- {flux_err}")

    # The scale_factor is the ratio of the photometric flux to the sbands flux taken from the spectrum
    scale_factor, scale_factor_err = umath.divide(flux, flux_err, sbands_fluxes[spec_key], 0)

    # Boost the scale_factor, so the resulting scaled spectra have arbitrary flux counts in a useful range
    #scale_factor, _ = umath.multiply(scale_factor, scale_factor_err, 1e23, 0)
    print(f"imarith ./calibrated/cal_{spec_key}.fits * {scale_factor} ./scaled/scaled_{spec_key}.fits")


