from data.PhotometryDataSource import *
from utility import timing as tm


class RateDataSource(PhotometryDataSource, ABC):
    """
    Abstract base class for Rate DataSources.
    """

    def _on_query(self, eruption_jd) -> DataFrame:
        # Make sure we work with a copy - we don't want to modify the underlying data
        df = self._data.copy()
        df = df.query("rate_err == rate_err").query("rate_err > 0")
        print(f"\tafter filtering out rate_err is NaN or 0, {len(df)} rows left")

        # We create the standard day and day_err fields, relative to passed eruption jd
        if "jd" in df.columns:
            df["day"] = tm.delta_t_from_jd(df["jd"], eruption_jd)
            df["day_err"] = df["jd_plus_err"]
        elif "mjd" in df.columns:
            df["day"] = tm.delta_t_from_jd(tm.jd_from_mjd(df["mjd"]), eruption_jd)
            df["day_err"] = df["mjd_plus_err"]

        return df
