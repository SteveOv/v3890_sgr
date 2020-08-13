import json
from fitting import *
from data import *
from plot import *
import spectra_lookup
from utility import novae as rn

settings = json.load(open("photometry.json"))

print(F"\n****************************************************************")
print(F"Ingesting, parsing and fitting data of RNe V3890 Sgr")
print(F"****************************************************************")
light_curves = {}
for data_source_key in settings["data_sources"]:
    ds_params = settings["data_sources"][data_source_key]
    ds = DataSource.create_from_config(ds_params)
    for lc_key in ds_params["light_curves"]:
        lc_params = ds_params["light_curves"][lc_key]

        # Each light_curve may have 1+ data_sets (equiv to bands or count types). Each a Dict under "set_params"
        if isinstance(ds, MagnitudeDataSource):
            data_sets_data = {}
            for set_params in lc_params['data_sets']:
                data_set_key = set_params['set']
                print(f"\nAnalysing {data_source_key}/{lc_key}/data_sets['{data_set_key}'] band data")
                # TODO: band query/filter goes into config (as it already is for rate sources)
                set_params["where"] = F"band=='{data_set_key}'"
                band_df = ds.query(lc_params['eruption_jd'], lc_params['query_params'], set_params)

                if "copy_fits" in set_params:
                    print(f"Copying the breaks/fits as already generated for {set_params['copy_fits']}")
                    fits = StraightLineLogXFitSet.copy(
                        light_curves[set_params['copy_fits']][data_set_key]['fits'],
                        x_shift=set_params['fit_x_shift'], y_shift=set_params['fit_y_shift'])
                else:
                    fits = StraightLineLogXFitSet.fit_to_data(band_df, "day", "mag", "mag_err", set_params['breaks'])

                # TODO: temporary way of telling downstream code what columns to use
                set_params["x_col"] = "day"
                set_params["y_col"] = "mag"
                set_params["y_err_col"] = "mag_err"
                data_sets_data[data_set_key] = {'df': band_df, 'fits': fits, 'params': set_params}
                print(fits)
            light_curves[F'{data_source_key}/{lc_key}'] = data_sets_data
        elif isinstance(ds, RateDataSource):
            data_set_data = {}
            for set_params in lc_params['data_sets']:
                data_set_key = set_params['set']

                print(f"\nAnalysing {data_source_key}/{lc_key}/data_sets['{data_set_key}'] rate data")
                type_df = ds.query(lc_params['eruption_jd'], lc_params['query_params'], set_params)
                # Use unweighted fitting for the XRT data
                if "breaks" in set_params and len(set_params["breaks"]) > 0:
                    fits = StraightLineLogLogFitSet.fit_to_data(type_df, "day", "rate",
                                                                y_err_col=None, breaks=set_params['breaks'])
                else:
                    fits = None

                # TODO: temporary way of telling downstream code what columns to use
                set_params["x_col"] = "day"
                set_params["y_col"] = "rate"
                set_params["y_err_col"] = "rate_err"
                data_set_data[data_set_key] = {'df': type_df, 'fits': fits, 'params': set_params}
                print(fits)
            light_curves[F"{data_source_key}/{lc_key}"] = data_set_data

print(F"\n\n****************************************************************")
print(F"Analysing combined Photometry to estimate distance to V3890 Sgr")
print(F"****************************************************************")
tt = []
for lc_key in ['2019-AAVSO/nominal-err', '2019-AAVSO/nominal+err', '2019-AAVSO/nominal']:
    print(f"Analysing photometry for light curve [{lc_key}]")
    bands_data = light_curves[lc_key]
    fitsV = light_curves[lc_key]['V']['fits']
    fitsB = light_curves[lc_key]['B']['fits']

    # Get the V-band peak, as tracking this will give us our distance modulus
    tp, V_tp = fitsV.find_peak_y_value(is_minimum=True)
    print(F"[{lc_key}] V-band peak; V(tp) = {V_tp:.4f} mag @ tp = t = {tp:.4f}")

    # Get the B-band at t(peak) too as this will give us our observed color
    B_tp = fitsB.find_y_value(tp)
    print(F"[{lc_key}] B-band at tp; B(tp) = {B_tp:.4f}")

    # Now we need the t2 time - the delta-t from peak when V has declined by 2 mag
    V_t2 = V_tp + 2
    t2 = fitsV.find_x_value(V_t2) - tp
    print(F"[{lc_key}] t2 time: t2 = t - tp = {t2:.4f} (when V = V(tp) + 2 = {V_t2:.4f} mag)")

    # Get the t3 time for information only - the delta-t from peak when V has declined by 3 mag
    V_t3 = V_tp + 3
    t3 = fitsV.find_x_value(V_t3) - tp
    print(F"[{lc_key}] t3 time: t3 = t - tp = {t3:.4f} (when V = V(tp) + 3 = {V_t3:.4f} mag)")

    # We can find the observed colour at tp - it's very blue (B > V)
    BV_obs_tp = B_tp - V_tp
    print(F"[{lc_key}] Observed colour at tp: (B-V)_obs(tp) = {B_tp:.4f} - {V_tp:.4f} = {BV_obs_tp:.4f}")

    # Work out the colour excess, E(B-V), at peak
    BV_int_tp = ufloat(0.23, 0.16)         # Bergh & Younger (1987)
    BV_int_t2 = ufloat(-0.02, 0.12)        # Bergh & Younger (1987)
    E_BV_tp = BV_int_tp - BV_obs_tp
    print(F"[{lc_key}] The colour excess @ tp: E(B-V)_tp = " +
          F"(B-V)_int(tp) - (B-V)_obs(tp) = ({BV_int_tp:.4f}) - ({BV_obs_tp:.4f}) = {E_BV_tp:.4f}")

    # Work out the colour excess, E(B-V), at t2
    B_t2 = fitsB.find_y_value(t2)
    BV_obs_t2 = B_t2 - V_t2
    E_BV_t2 = BV_int_t2 - BV_obs_t2
    print(F"[{lc_key}] The colour excess @ t2: E(B-V)_t2 = " +
          F"(B-V)_int(t2) - (B-V)_obs(t2) = ({BV_int_t2:.4f}) - ({BV_obs_t2:.4f}) = {E_BV_t2:.4f}")

    # The E(B-V) calculated above, from intrinsic_BV figures of Bergh & Younger, imply that here we are
    # seeing greater extinction for red than blue light.  That's rather at odds with existing findings/expectations!
    # Instead, I'm going to use Schaefer's E(B-V) of 0.9 +/- 0.3 for subsequent calculations.
    E_BV = ufloat(0.9, 0.3)
    print(F"[{lc_key}] The calculated colour excess is unrealistic: using E(B-V) = {E_BV:.4f} from Schaefer (2010)")

    # Now use the MMRD to work out the absolute magnitude
    M_V_tp = rn.absolute_magnitude_from_t2_fast_nova(t2)
    print(F"[{lc_key}] Peak absolute magnitude from MMRD: M_V(tp) = {M_V_tp:.4f} mag")

    # And the distance modulus from th apparent and absolute magnitudes
    mu = V_tp - M_V_tp
    print(F"[{lc_key}] Distance modulus: mu = V(tp) - M_V(tp) = {V_tp:.4f} - {M_V_tp:.4f} = {mu:.4f}s")

    # And finally the distance
    R_V = 3.1
    A_V = E_BV * R_V
    print(f"[{lc_key}] The extinction is A_V = E(B-V) * R_V = {E_BV:.4f} * 3.1 = {A_V:.4f}")
    d = 10**(0.2 * (mu + 5 - A_V))
    print(F"[{lc_key}] The distance is: d = 10^(0.2(mu + 5 - A_V)) = {d:.1f} pc")
    print()

    tt.append({"key": lc_key, "tp": tp, "t2": t2, "t3": t3, "E_BV": E_BV, "M_V_tp": M_V_tp, "d": d})

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
print(F"Producing Plots of data on to V3890 Sgr")
print(F"****************************************************************")
# Produce any configured plots
for plot_group_config in settings["plots"]:
    print(F"\nProcessing plot group: {plot_group_config}")
    for plot_config in settings["plots"][plot_group_config]:

        # Pass on some calculated parameters to the plots - these are from the nominal fits (which is run last)
        plot_config["params"]["eruption_jd"] = eruption_jd = 2458723.278
        plot_config["params"]["E(B-V)"] = E_BV
        plot_config["params"]["A_V"] = A_V
        plot_config["params"]["distance_pc"] = d
        plot_config["params"]["mu"] = mu
        epochs = spectra_lookup.get_spectra_epochs(eruption_jd)

        plot_data = PlotHelper.create_plot_data_from_config(plot_config, light_curves, epochs)
        PlotHelper.plot_to_file(plot_config, plot_data=plot_data)