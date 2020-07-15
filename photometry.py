import json
import magnitudes as mag
import novae as rn
from fitting import *
from data import *
from plot import *

settings = json.load(open("./photometry_settings.json"))

print(F"\n****************************************************************")
print(F"Ingesting, parsing and fitting data of RNe V3890 Sgr")
print(F"****************************************************************")
light_curves = {}
for data_source_key in settings["data_sources"]:
    ds_params = settings["data_sources"][data_source_key]
    ds_type = ds_params["type"]
    file_spec = ds_params["file_spec"]

    ds = DataSource.create(ds_type, file_spec)
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
                if "breaks" in set_params and len(set_params["breaks"]) > 0:
                    fits = StraightLineLogLogFitSet.fit_to_data(type_df, "day", "rate", "rate_err", set_params['breaks'])
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
print(F"Producing Plots of data on to V3890 Sgr")
print(F"****************************************************************")
# Produce any configured plots
for plot_group_config in settings["plots"]:
    print(F"\nProcessing plot group: {plot_group_config}")
    for plot_config in settings["plots"][plot_group_config]:
        plot_data = PlotHelper.create_plot_data_from_config(plot_config, light_curves)
        PlotHelper.plot_to_file(plot_config, plot_data)

# TODO: work out the t0, t2 and t3 times for the V-band
print(F"\n\n****************************************************************")
print(F"Analysing combined Photometry to estimate distance to V3890 Sgr")
print(F"****************************************************************")
tt = []
for lc_key in ['2019-AAVSO/nominal', '2019-AAVSO/nominal-err', '2019-AAVSO/nominal+err']:
    print(f"Analysing photometry for light curve [{lc_key}]")
    bands_data = light_curves[lc_key]
    fitsV = light_curves[lc_key]['V']['fits']
    fitsB = light_curves[lc_key]['B']['fits']

    # Get the V-band peak, as tracking this will give us our distance modulus
    t0, V_t0 = fitsV.find_peak_y_value(is_minimum=True)
    print(F"[{lc_key}] V-band peak; V_t0 = {V_t0:.4f} mag @ t0 = {t0:.4f}")

    # Now we need the t2 time - first get the mag two declined from peak
    V_t2 = V_t0 + 2
    t2 = fitsV.find_x_value(V_t2)
    print(F"[{lc_key}] V-band decline: V_t2 = {V_t2:.4f} mag @ t2 = {t2:.4f}")

    # Get the t3 time for information only
    t3 = fitsV.find_x_value(V_t0 + 3)

    # Now find the magnitude in the B-band at the V-band t2 time, so we can work out the (B-V)_obs,t2 colour
    B_t2 = fitsB.find_y_value(t2)
    print(F"[{lc_key}] B-band magnitude at t2: B_t2 = {B_t2:.4f} mag")

    # So now we can find the observed colour at t_2
    observed_BV_t2 = B_t2 - V_t2
    print(F"[{lc_key}] Observed colour at t2: (B-V)_obs,t2 = {B_t2:.4f} - {V_t2:.4f} = {observed_BV_t2:.4f}")

    # Work out the colour excess, E(B-V), at peaks
    intrinsic_BV_t0 = ufloat(0.23, 0.16)         # Bergh & Younger (1987)
    intrinsic_BV_t2 = ufloat(-0.02, 0.12)        # Bergh & Younger (1987)
    E_BV = observed_BV_t2 - intrinsic_BV_t2
    print(F"[{lc_key}] The colour excess at peak is E(B-V) = (B-V)obs - (B-V)int = "
          + "({observed_BV_t2:.4f}) - ({intrinsic_BV_t2:.4f}) = {E_BV:.4f}")

    # Now use the MMRD to work out the absolute magnitude
    M_V_t0 = rn.absolute_magnitude_from_t2_fast_nova(t2)
    print(F"[{lc_key}] Peak absolute magnitude from MMRD: M_V_t0 = {M_V_t0:.4f} mag")

    # And the distance modulus from th apparent and absolute magnitudes
    mu = V_t0 - M_V_t0
    print(F"[{lc_key}] Distance modulus: mu = V_t0 - M_V_t0 = {V_t0:.4f} - {M_V_t0:.4f} = {mu:.4f}s")

    # And finally the distance
    A_V = mag.extinction_from_color(E_BV, 3.1)
    d = mag.distance_from_magnitudes(V_t0, M_V_t0, A_V)
    print(F"[{lc_key}] The distance is: d = 10^(0.2(mu + 5 - E_BV*A_V)) = {d:.1f} pc")
    print()

    tt.append({"key": lc_key, "t0": t0, "t2": t2, "t3": t3, "E_BV": E_BV, "M_V_t0": M_V_t0, "d": d})

# Summary
df_sum = pd.DataFrame.from_records(tt, columns=["key", 't0', 't2', 't3', 'E_BV', "M_V_t0", "d"])
print("Summary of the 2019 eruption")
print(F"[2019] t_eruption (JD) = 2458723.278+/-0.256")
print(F"[2019] t_0 = {ufloat(.35, .25):.3} d")
print(F"[2019] <t_2> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['t2']), unumpy.std_devs(df_sum['t2']))):.3f} d")
print(F"[2019] <t_3> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['t3']), unumpy.std_devs(df_sum['t3']))):.3f} d")
print(F"[2019] <E_BV> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['E_BV']), unumpy.std_devs(df_sum['E_BV']))):.3f}")
print(F"[2019] <M_V_t0> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['M_V_t0']), unumpy.std_devs(df_sum['M_V_t0']))):.4f} mag")
print(F"[2019] <d> = {np.mean(unumpy.uarray(unumpy.nominal_values(df_sum['d']), unumpy.std_devs(df_sum['d']))):.0f} pc")
