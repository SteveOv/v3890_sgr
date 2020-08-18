import json
from data.CalibratedSpectralDataSource import *
from plot import *
from utility import timing as tm

# Placeholder for pulling together all of the spectroscopy tasks
settings = json.load(open("spectroscopy.json"))
line_sets = settings["line_sets"]
eruption_jd = 2458723.278

# Run the plots
for plot_group_config in settings["plots"]:
    print(F"\nProcessing plot group: {plot_group_config}")
    for plot_config in settings["plots"][plot_group_config]:
        # Create the requested spectral data sources and get the data from them
        spectra = []
        spectral_lines = {}
        delta_t = None
        for spec_name in plot_config["spectra"]:
            ds = DataSource.create_from_config(settings["data_sources"][spec_name], "CalibratedSpectralDataSource")
            delta_t = tm.delta_t_from_jd(tm.jd_from_mjd(ds.header["MJD"]), eruption_jd)
            spectrum = ds.query()
            print(f"\tUsing spectrum '{spec_name}': Delta-t={delta_t:.2f} & max_flux={spectrum.max_flux}")
            spectra.append(spectrum)

        # Build the list of spectral lines which will overlay the spectra
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
        plot_config["params"]["y_lim"] = [-1, 100]
        plot_config["title"] = \
            f"Sky-subtracted, calibrated, scaled and de-reddened spectra at $\\Delta t={delta_t:.2f}$ d"
        PlotHelper.plot_to_file(plot_config, spectra=spectra, spectral_lines=spectral_lines)



