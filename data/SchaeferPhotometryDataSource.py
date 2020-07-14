import pandas as pd
from uncertainties import ufloat, unumpy, ufloat_fromstr
from data.MagnitudeDataSource import *


class SchaeferMagnitudeDataSource(MagnitudeDataSource):
    """
    Read and parse Photometry Data files publishes as part of
    Schaefer (2010) Comprehensive Photometric Histories of all Known Galactic RNe
    """

    def _ingest(self, source: str) -> DataFrame:
        """
        Ingest the data from the specified source and return it as a pandas DataFrame
        with the following standard fields
            jd
            mag
            mag_err
            band
            observer_code
            is_null_obs
            is_saturated_obs
        """
        # Read the file in.  We use a UFloat to parse the magnitude field
        df = pd.read_csv(source, skiprows=lambda x: x in [0, 1, 2, 4], header=0, delimiter="\t", index_col=None,
                         converters={"Magnitude": SchaeferMagnitudeDataSource._to_ufloat})

        # Standardise column names without spaces
        df.columns = [col.replace(' ', '_') for col in df.columns]

        # Covers the expected jd and band columns
        df.rename(columns={"Julian_Date": "jd", "Band": "band"}, inplace=True)

        # Magnitude data is stored as nominal +/- sigma which we parse with a UFloat and then split here
        df['mag'] = unumpy.nominal_values(df['Magnitude'])
        df['mag_err'] = unumpy.std_devs(df['Magnitude'])
        df['is_null_obs'] = np.isnan(df['mag'])

        df['observer_code'] = ""
        df['is_saturated_obs'] = ""
        return df

    @classmethod
    def _to_ufloat(cls, value):
        if value.startswith('>'):
            return ufloat(float("NaN"), 0)
        else:
            return ufloat_fromstr(value.replace("+or-", "+/-"))
