import numpy as np
from data.PhotometryDataSource import *


class RateDataSource(PhotometryDataSource, ABC):
    """
    Abstract base class for Rate DataSources.
    """

    def _on_query(self, eruption_jd) -> DataFrame:
        # Make sure we work with a copy - we don't want to modify the underlying data
        df = self._df.copy()
        df = df.query("rate_err == rate_err").query("rate_err > 0")
        print(f"\tafter filtering out rate_err is NaN or 0, {len(df)} rows left")

        # We create the standard day and day_err fields, relative to passed eruption jd
        df["day"] = np.subtract(np.add(df["jd"], 2400000), eruption_jd)
        df["day_err"] = df["jd_plus_err"]
        return df
