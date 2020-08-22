import json
from data import DataSource, CalibratedSpectralDataSource
from plot import *
from utility import timing as tm
from spectroscopy import line_fitting

# Placeholder for pulling together all of the spectroscopy tasks
settings = json.load(open("spectroscopy.json"))
line_sets = settings["line_sets"]
eruption_jd = 2458723.278

print(F"\n\n****************************************************************")
print(F"* Ingesting data and creating the spectroscopy data sources.")
print(F"****************************************************************")
data_sources = {}
for spec_name, ds_config in settings["data_sources"].items():
    data_sources[spec_name] = DataSource.create_from_config(ds_config, "CalibratedSpectralDataSource")

print(F"\n\n****************************************************************")
print(F"* Fitting spectral lines and deriving parameters.")
print(F"****************************************************************")
line_fit_sets = {}
line_fit_sets["b_e_20190905_7"] = line_fitting.fit_b_e_20190905_7(data_sources["b_e_20190905_7"].query())
line_fit_sets["r_e_20190905_7"] = line_fitting.fit_r_e_20190905_7(data_sources["r_e_20190905_7"].query())

print(F"\n\n****************************************************************")
print(F"* Producing plots of spectroscopy data and lines ")
print(F"****************************************************************")
for plot_group_config in settings["plots"]:
    print(F"\nProcessing plot group: {plot_group_config}")
    flux_units = mag.units_flux_density_cgs_angstrom
    for plot_config in settings["plots"][plot_group_config]:
        # Create the requested spectral data sources and get the data from them
        spectra = {}
        spectral_lines = {}
        plot_line_fits = {}
        delta_t = None
        for spec_name in plot_config["spectra"]:
            ds = data_sources[spec_name]
            delta_t = tm.delta_t_from_jd(tm.jd_from_mjd(ds.header["MJD"]), eruption_jd)
            spectrum = ds.query()
            print(f"\tUsing spectrum '{spec_name}': Delta-t={delta_t:.2f} & max_flux={spectrum.max_flux}")
            spectra[spec_name] = ds.query()
            flux_units = spectrum.flux.unit

            # Pick up any fitted spectral lines taken from this spectrum
            if spec_name in line_fit_sets:
                plot_line_fits[spec_name] = line_fit_sets[spec_name]

        # Build the list of known emission lines which will overlay the spectra
        if "spectral_lines" in plot_config:
            print(f"Selecting spectral_lines to overlay on plot.")
            for line_set_name in plot_config["spectral_lines"]:
                if line_set_name in line_sets:
                    line_set = line_sets[line_set_name]
                    named_lines = plot_config["spectral_lines"][line_set_name]
                    for named_line in named_lines:
                        if named_line in line_set:
                            spectral_lines[named_line] = line_set[named_line]
                        else:
                            print(f"** named_line '{named_line}' does not exist in line_set '{line_set_name}'")
                else:
                    print(f"** unknown line_set: {line_set_name}")

        # Do the print!
        plot_config["params"]["y_lim"] = [-1e-12, 21e-12]
        plot_config["params"]["y_ticks"] = [0, 5e-12, 10e-12, 15e-12, 20e-12]
        plot_config["params"]["y_tick_labels"] = ["0", "5", "10", "15", "20"]
        plot_config["params"]["y_label"] = f"Flux density [$10^{{-12}}$ {flux_units:latex_inline}]"
        plot_config["title"] = \
            f"Sky-subtracted, calibrated, scaled and de-reddened spectra at $\\Delta t={delta_t:.2f}$ d"
        PlotHelper.plot_to_file(plot_config, spectra=spectra, line_fits=plot_line_fits, spectral_lines=spectral_lines)
