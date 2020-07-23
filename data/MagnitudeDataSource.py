import numpy as np
import with_uncertainties as unc
from data.PhotometryDataSource import *


class MagnitudeDataSource(PhotometryDataSource, ABC):

    vega_fluxes = {
                "B": 4000,
                "V": 3600,
                "R": 3060,
                "I": 2420
            }

    def _on_query(self, eruption_jd: float) -> DataFrame:
        """
        Return standard magnitude fields for use by a magnitude query.
        """
        # Make sure we are working with a copy of the underlying data - we don't want to change the source
        df = self._df.copy()

        # Apply any filters; the two on mag_err exclude those rows where mag_err is NaN and 0 (both no use to us)
        df = df.query("mag_err == mag_err").query("mag_err > 0").query("is_null_obs == False")
        print(f"\tafter filtering on mag_err is NaN or 0 and is_null_obs == True, {len(df)} rows left")

        # We create day and log(day) field, relative to passed eruption jd
        df['day'] = np.subtract(df['jd'], eruption_jd)
        df['log_day'] = np.log10(df.query("day>0")['day'])

        """ Currently not required (also, this is quite slow)
        # If not already present, calculate flux density values for the retrieved data.
        if "flux_hz" not in df.columns:
            df[['flux_hz', "flux_hz_err"]] = df.apply(
                lambda d: MagnitudeDataSource.flux_density_from_magnitude(d["mag"], d["mag_err"], d["band"]),
                axis=1,
                result_type="expand")
        """
        return df

    @classmethod
    def flux_density_from_magnitude(cls, mag, mag_err, band):

        f_vega = cls.vega_fluxes[band] if band in cls.vega_fluxes else 0

        n, n_err = unc.divide(mag, -2.5, mag_err, 0)
        n, n_err = unc.power(10, n, 0, n_err)
        f_nu, f_nu_err = unc.multiply(n, f_vega, n_err, 0)

        return f_nu, f_nu_err


