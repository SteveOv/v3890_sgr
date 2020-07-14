import numpy as np
from data.DataSource import *


class MagnitudeDataSource(DataSource, ABC):

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
        return df

