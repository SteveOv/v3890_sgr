import json
from copy import deepcopy
from fitting import *
from data import *
from plot import *
import spectra_lookup
from utility import novae as rn, magnitudes as mag

settings = json.load(open("photometry.json"))

print(F"\n\n****************************************************************")
print(F"* Ingesting data and creating the photometry data sources.")
print(F"****************************************************************")
data_sources = {}
for data_source_key in settings["data_sources"]:
    ds_config = settings["data_sources"][data_source_key]
    data_sources[data_source_key] = DataSource.create_from_config(ds_config)

print(F"\n\n****************************************************************")
print(F"* Querying photometry data and to extract lightcurves.")
print(F"****************************************************************")
lightcurves = {}
for grp_key, grp_config in settings["lightcurve_groups"].items():
    print(F"\nProcessing Lightcurve group: {grp_key}")
    data_source = data_sources[grp_config["data_source"]]
    for lc_key in grp_config["lightcurves"]:
        lightcurves[f"{grp_key}/{lc_key}"] = Lightcurve.create_from_data_source(lc_key, data_source, grp_config)

print(F"\n\n****************************************************************")
print(F"* Parsing photometry data and creating fitted light curves.")
print(F"****************************************************************")
fit_sets = {}
for grp_key, grp_config in settings["fit_set_groups"].items():
    print(F"\nProcessing FitSet group: {grp_key}")
    if "copy_fit_sets" in grp_config:
        copy_fits_config = grp_config["copy_fit_sets"]
        # Rather than generating new from lightcurves we are copying, and optionally translating, existing fit_sets.
        for key_match, copy_config in copy_fits_config.items():
            matches = {k: v for k, v in lightcurves.items() if k.startswith(key_match)}
            for fit_set_key in matches:
                source_fit_set = fit_sets[fit_set_key]
                x_shift = copy_config["x_shift"] if "x_shift" in copy_config else 0
                y_shift = copy_config["y_shift"] if "y_shift" in copy_config else 0
                copy_fit_set = FitSet.copy(source_fit_set, x_shift=x_shift, y_shift=y_shift)
                fit_sets[f"{grp_key}/{copy_fit_set.name}"] = copy_fit_set

    if "lightcurve_group" in grp_config:
        # FitSets grouped by shared DataSource, eruption & query parameters.  Resulting key is group key/set key
        lightcurve_grp_key = grp_config["lightcurve_group"]
        fit_set_type = grp_config["type"] if "type" in grp_config else "StraightLineLogXFitSet"

        for fit_set_key, fit_set_config in grp_config["fit_sets"].items():
            # Get the lightcurve to base this fit on.  Either it's explicit or it's implied by the name and group
            lightcurve_key = fit_set_config["lightcurve"] if "lightcurve" in fit_set_config else f"{lightcurve_grp_key}/{fit_set_key}"
            lightcurve = lightcurves[lightcurve_key]

            # Currently there are only two types, so no factory implemented.
            fit_set = None
            if fit_set_type == "StraightLineLogXFitSet":
                fit_set = StraightLineLogXFitSet.fit_to_data(
                    fit_set_key, lightcurve, x_col="day", y_col="mag", y_err_col="mag_err", breaks=fit_set_config['breaks'])
            elif fit_set_type == "StraightLineLogLogFitSet":
                # We use unweighted fits for the XRT/Rate data
                y_err_col = "mag_err" if lightcurve.data_type != "rate" else None
                fit_set = StraightLineLogLogFitSet.fit_to_data(
                    fit_set_key, lightcurve, x_col="day", y_col="rate", y_err_col=y_err_col, breaks=fit_set_config['breaks'])

            if fit_set is not None:
                fit_set.metadata.conflate(lightcurve.metadata)
                fit_sets[f"{grp_key}/{fit_set_key}"] = fit_set

for fit_set_key, fit_set in fit_sets.items():
    print(f"\n\t\tFit set {fit_set_key}\n{fit_set.to_latex()}\n")

print(F"\n\n****************************************************************")
print(F"* Analysing photometry data and fitted light curves ")
print(F"****************************************************************")
tt = []
for group_key in ['V3890-Sgr-2019-Vis-nominal-err', 'V3890-Sgr-2019-Vis-nominal+err', 'V3890-Sgr-2019-Vis-nominal']:
    print(f"Analysing photometry for light curve [{group_key}]")
    fitsV = fit_sets[f"{group_key}/V-band"]
    fitsB = fit_sets[f"{group_key}/B-band"]

    # Get the V-band peak, as tracking this will give us our distance modulus
    tp, V_tp = fitsV.find_peak_y_value(is_minimum=True)
    print(F"[{group_key}] V-band peak; V(tp) = {V_tp:.4f} mag @ tp = t = {tp:.4f}")

    # Get the B-band at t(peak) too as this will give us our observed color
    B_tp = fitsB.find_y_value(tp)
    print(F"[{group_key}] B-band at tp; B(tp) = {B_tp:.4f}")

    # Now we need the t2 time - the delta-t from peak when V has declined by 2 mag
    V_t2 = V_tp + 2
    t2 = fitsV.find_x_value(V_t2) - tp
    print(F"[{group_key}] t2 time: t2 = t - tp = {t2:.4f} (when V = V(tp) + 2 = {V_t2:.4f} mag)")

    # Get the t3 time for information only - the delta-t from peak when V has declined by 3 mag
    V_t3 = V_tp + 3
    t3 = fitsV.find_x_value(V_t3) - tp
    print(F"[{group_key}] t3 time: t3 = t - tp = {t3:.4f} (when V = V(tp) + 3 = {V_t3:.4f} mag)")

    # We can find the observed colour at tp - it's very blue (B > V)
    BV_obs_tp = B_tp - V_tp
    print(F"[{group_key}] Observed colour at tp: (B-V)_obs(tp) = {B_tp:.4f} - {V_tp:.4f} = {BV_obs_tp:.4f}")

    # Work out the colour excess, E(B-V), at peak
    BV_int_tp = ufloat(0.23, 0.16)         # Bergh & Younger (1987)
    BV_int_t2 = ufloat(-0.02, 0.12)        # Bergh & Younger (1987)
    E_BV_tp = BV_obs_tp - BV_int_tp
    print(F"[{group_key}] Calculating colour excess wrt Bergh & Younger (B-V)_int values at t_p and t_0")
    print(F"[{group_key}] The colour excess @ tp: E(B-V)_tp = " +
          F"(B-V)_obs(tp) - (B-V)_int(tp) = ({BV_obs_tp:.4f}) - ({BV_int_tp:.4f}) = {E_BV_tp:.4f}")

    # Work out the colour excess, E(B-V), at t2
    B_t2 = fitsB.find_y_value(t2)
    BV_obs_t2 = B_t2 - V_t2
    E_BV_t2 = BV_obs_t2 - BV_int_t2
    print(F"[{group_key}] The colour excess @ t2: E(B-V)_t2 = " +
          F"(B-V)_obs(t2) - (B-V)_int(t2) = ({BV_obs_t2:.4f}) - ({BV_int_t2:.4f}) = {E_BV_t2:.4f}")

    # Significantly lower than Schaefer's E(B-V) of 0.9 +/- 0.3.
    # As recommended by Matt Darnley (private communication), we use the Pan-STARRS reddening survey along
    # alpha=277.68, delta=-24.019 for r>5 kpc (which V380 Sgr has with even E(B-V)=0.9) giving E(g-r)=0.51 +/- 0.02
    E_BV = ufloat(*mag.E_gr_to_E_BV(0.51, 0.02))
    print(F"[{group_key}] Using E(B-V) = {E_BV:.4f} (derived from Pan-STARRS E(g-r) = 0.51 +/- 0.02)")

    # Now use the MMRD to work out the absolute magnitude
    M_V_tp = rn.absolute_magnitude_from_t2_fast_nova(t2)
    print(F"[{group_key}] Peak absolute magnitude from MMRD: M_V(tp) = {M_V_tp:.4f} mag")

    # And the distance modulus from th apparent and absolute magnitudes
    mu = V_tp - M_V_tp
    print(F"[{group_key}] Distance modulus: mu = V(tp) - M_V(tp) = {V_tp:.4f} - {M_V_tp:.4f} = {mu:.4f}s")

    # And finally the distance
    R_V = 3.1
    A_V = E_BV * R_V
    print(f"[{group_key}] The extinction is A_V = E(B-V) * R_V = {E_BV:.4f} * 3.1 = {A_V:.4f}")
    d = 10**(0.2 * (mu + 5 - A_V))
    print(F"[{group_key}] The distance is: d = 10^(0.2(mu + 5 - A_V)) = {d:.1f} pc")
    print()

    tt.append({"key": group_key, "tp": tp, "t2": t2, "t3": t3, "E_BV": E_BV, "M_V_tp": M_V_tp, "d": d})

# Summary
df_sum = pd.DataFrame.from_records(tt, columns=["key", 'tp', 't2', 't3', 'E_BV', "M_V_tp", "d"])
print("Summary of the 2019 eruption")
print(F"[2019] t_eruption (JD) = 2458723.278+/-0.256")
#print(F"[2019] tp = {ufloat(.35, .25):.3} d")
print(F"[2019] <tp> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['tp']), unumpy.std_devs(df_sum['tp']))):.3f} d")
print(F"[2019] <t2> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['t2']), unumpy.std_devs(df_sum['t2']))):.3f} d")
print(F"[2019] <t3> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['t3']), unumpy.std_devs(df_sum['t3']))):.3f} d")
print(F"[2019] <E(B-V)> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['E_BV']), unumpy.std_devs(df_sum['E_BV']))):.3f}")
print(F"[2019] <M_V_tp> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['M_V_tp']), unumpy.std_devs(df_sum['M_V_tp']))):.4f} mag")
print(F"[2019] <d> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['d']), unumpy.std_devs(df_sum['d']))):.0f} pc")

print(F"\n\n****************************************************************")
print(F"* Producing plots of photometry data and fitted light curves ")
print(F"****************************************************************")
# Produce any configured plots
for grp_key in settings["plot_groups"]:
    print(F"\nProcessing plot group: {grp_key}")
    group_config = settings["plot_groups"][grp_key]
    for plot_config in group_config:

        # Pass on some calculated parameters to the plots - these are from the nominal fits (which is run last)
        plot_config["params"]["eruption_jd"] = eruption_jd = 2458723.278
        plot_config["params"]["E(B-V)"] = E_BV
        plot_config["params"]["A_V"] = A_V
        plot_config["params"]["distance_pc"] = d
        plot_config["params"]["mu"] = mu
        epochs = spectra_lookup.get_spectra_epochs(eruption_jd)

        # Get the lightcurves for this plot
        plot_lightcurves = {}
        for key_match, metadata_overrides in plot_config["lightcurves"].items():
            # Get all the matching lightcurves
            matches = {k: v for k, v in lightcurves.items() if k.startswith(key_match)}
            for key in matches:
                lightcurve = deepcopy(lightcurves[key])
                lightcurve.metadata.conflate(metadata_overrides)
                plot_lightcurves[key] = lightcurve

        # Get the FitSets for this plot
        plot_fit_sets = {}
        for key_match, metadata_overrides in plot_config["fit_sets"].items():
            # Get all the matching FitSets and
            matches = {k: v for k, v in fit_sets.items() if k.startswith(key_match)}
            for key, item in matches.items():
                fit_set = deepcopy(fit_sets[key])
                fit_set.metadata.conflate(metadata_overrides)
                plot_fit_sets[key] = fit_set

        PlotHelper.plot_to_file(plot_config, lightcurves=plot_lightcurves, fit_sets=plot_fit_sets, epochs=epochs)
