from typing import Dict
from pandas import DataFrame
from matplotlib.axes import Axes
from plot import TimePlotSupportingLogAxes
from astropy.modeling.models import Gaussian1D
from spectroscopy import fit_utilities as fu
from utility import timing as tm


class SpectralLineVelocityTimePlot(TimePlotSupportingLogAxes):

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_x_label = "$\\Delta t$ [days]"
        self._default_y_label = "Velocity dispersion [km / s]"
        self._default_x_lim = [0, 30]
        self._default_x_ticks = [0, 5, 10, 15, 20, 25, 30]

        self._default_lines = {
            "H$\\alpha$": {
                "fit$_{1}$": {"color": "darkred", "label": "wide base"},
                "fit$_{2}$": {"color": "r", "label": "narrow peak"}
            },
            "H$\\beta$": {
                "fit$_{1}$": {"color": "darkblue", "label": "wide base"},
                "fit$_{2}$": {"color": "b", "label": "narrow peak"}
            },
            "He II (4686)": {
                "fit$_{1}$": {"color": "darkcyan", "label": "wide base"},
                "fit$_{2}$": {"color": "cyan", "label": "narrow peak"}
            }
        }

        self._default_eruption_jd = 2458723.278
        return

    @property
    def lines(self):
        return self._param("lines", self._default_lines)

    @property
    def eruption_jd(self):
        return self._param("eruption_jd", self._default_eruption_jd)

    def _draw_plot_data(self, ax: Axes, **kwargs):
        # The payload should be spectral line fitted models containing Gaussian fits to lines. It's a dictionary keyed
        # on spec_name (b_e_20190828_3 etc.).  Each item is an array of astropy CompoundModels for each spectral line.
        # Each model will have 1+ Gaussian1D models for the line and 1 Polynomial1D for the continuum.
        # Compound models named H$\\alpha$ etc.  Each Gaussian fit$_{1}$ (wide), fit$_{2}$ (narrow)
        spectra = kwargs["spectra"]
        all_line_fits = kwargs["line_fits"]
        reference_jd = self.eruption_jd

        # The data is in a slightly awkward form, dicts keyed on spectrum with each item an array of line_fits (as we
        # would generally be interested in one spectrum & associated data at a time). Best to transform into a
        # more usable form; an array of dictionaries which can be loaded into a DataFrame / tabular data
        rows = list()
        columns = ["line", "fit", "delta_t", "velocity", "velocity_err"]
        for spec_key, line_fits in all_line_fits.items():
            mjd = spectra[spec_key].mjd if spec_key in spectra else None
            delta_t = tm.delta_t_from_jd(tm.jd_from_mjd(mjd), reference_jd=reference_jd)
            for line_fit in line_fits:
                if line_fit.name in self.lines:
                    for sub_fit in line_fit:
                        if sub_fit.name in self.lines[line_fit.name] and isinstance(sub_fit, Gaussian1D):
                            lambda_0 = sub_fit.mean.quantity
                            v = fu.calculate_velocity_from_sigma(lambda_0, sub_fit.stddev.quantity).to("km / s")
                            v_err = 0 * v.unit  # TODO: uncertainty
                            rows.append({
                                "line": line_fit.name.replace("\\", "_"),
                                "fit": sub_fit.name.replace("\\", "_"),
                                "delta_t": delta_t,
                                "velocity": v.value,
                                "velocity_err": v_err.value
                            })
        df = DataFrame.from_records(rows, columns=columns)

        # The line name / fit name will be used to look up the corresponding columns
        for line_name, line in self.lines.items():
            line_field = line_name.replace("\\", "_")
            for fit_name, fit_plot_params in line.items():
                color = fit_plot_params["color"] if "color" in fit_plot_params else "k"
                label = f"{line_name} {fit_plot_params['label'] if 'label' in fit_plot_params else fit_name}"
                fit_field = fit_name.replace("\\", "_")

                df_line = df.query(f"line == '{line_field}' and fit == '{fit_field}'").sort_values(by="delta_t")
                if len(df_line) > 0:
                    self._plot_df_to_error_bars_on_ax(ax, df, "delta_t", "velocity", "velocity_err", color, label)
        return
