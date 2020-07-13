import numpy as np
from data.DataSource import *


class RateDataSource(DataSource, ABC):

    def query_rates(self, eruption_jd, query_params: Dict, set_params: Dict) -> DataFrame:

        df = self._on_query_rates()

        # We create day and log(day) field, relative to passed eruption jd
        df['day'] = np.subtract(np.add(df['jd'], 2400000), eruption_jd)
        df['day_err'] = df['jd_plus_err']

        # TODO: temp
        df['rate_err'] = df['rate_plus_err']

        # Now apply any query filters
        for query_key in query_params:
            if query_key == "day_range":
                day_range = query_params[query_key]
                df = df.query(f"day >= {day_range[0]}").query(f"day <= {day_range[1]}")
                print(f"\tafter filtering on {day_range[0]} <= day <= {day_range[1]}, we now have {len(df)} rows")

        return df[["jd", "day", "log_day", "day_err", "log_day_err", "rate", "rate_err", "rate_type"]]

    @abstractmethod
    def _on_query_rates(self) -> DataFrame:
        """
        Implemented by subclass to get data into a state for querying by count.
        """
        pass
