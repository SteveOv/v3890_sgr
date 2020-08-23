import pandas as pd
from data.MagnitudeDataSource import *


class AavsoMagnitudeDataSource(MagnitudeDataSource):
    """
    Read and parse AAVSO Photometry Data files into pandas DataFrames
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
        source = self.__class__._canonicalize_filename(source)
        df = pd.read_csv(source, header=0, index_col=None)
        print(f"\tRead in {len(df)} row(s) from {source}")

        first = min(df["JD"])
        last = max(df["JD"])
        print(f"\tData covers time period JD={first} ({tm.date_time_from_jd(first)}) to JD={last} ({tm.date_time_from_jd(last)})")

        # Standardise column names as lower case without spaces - makes them easier to work with.
        # This gives us the standard jd, band and observer_code fields.
        df.columns = [col.replace(' ', '_').lower() for col in df.columns]

        # Magnitude field is generally numeric, but has format like <12.5 where null observation
        # (below observable magnitude). We create a new flag field to make it easy to spot
        df['is_null_obs'] = AavsoMagnitudeDataSource._is_null_observation(df['magnitude'])
        df['mag'] = pd.to_numeric(df['magnitude'], errors='coerce')
        df['mag_err'] = pd.to_numeric(df['uncertainty'], errors='coerce')

        # No specific saturated field in this data
        df['is_saturated_obs'] = False

        # We are only interested in measurement_methods which indicate target has been calibrated against standards.
        # Other values, excluded; DIFF - req' Comp Star 1 to standardize, STEP un-reduced step magnitude
        # The validation flag indicates; V - fully validated, Z - pre-validated, T - discrepancy, U - unvalidated.
        # We exclude T & U (excluding Z leaves very little data and nothing usable for the 2019 eruption of V3890 Sgr).
        print("\tIngesting only those observations calibrated against a standard and where validated/pre-validated.")
        df = df.query("measurement_method in 'STD' and validation_flag in ['V', 'Z']")
        return df[["jd", "mag", "mag_err", "band", "observer_code", "is_null_obs", "is_saturated_obs"]]

    @classmethod
    def _is_null_observation(cls, value):
        return value.str.startswith('<')

    @classmethod
    def _to_magnitude(cls, value):
        if cls._is_null_observation(value):
            return np.nan
        else:
            return float(value)
