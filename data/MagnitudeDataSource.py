import numpy as np
from data.DataSource import *


class MagnitudeDataSource(DataSource, ABC):

    def query_magnitudes(self, eruption_jd: str, query_params: Dict) -> DataFrame:
        """
        Read from this data source, with days/log_days referenced to the passed eruption_jd.
        Apply any query filters defined in the passed query params dictionary.
        """
        print(F"{self.__class__.__name__}: Reading & filtering on t_eruption (JD)={eruption_jd} and {query_params}")

        # Apply any filters the two on mag_err exclude those rows where mag_err is NaN and 0 (both no use to us)
        df = self._on_query_magnitudes().query("mag_err == mag_err").query("mag_err > 0").query("is_null_obs == False")
        print(f"\tafter filtering on mag_err is NaN or 0 and is_null_obs == True, we now have {len(df)} rows")

        # We create day and log(day) field, relative to passed eruption jd
        df['day'] = np.subtract(df['jd'], eruption_jd)
        df['log_day'] = np.log10(df.query("day>0")['day'])

        for query_key in query_params:
            if query_key == "filter":
                # Generic filter/query expression in the form "field == value"
                df = df.query(query_params["filter"])
            elif query_key == "day_range":
                day_range = query_params[query_key]
                df = df.query(f"day >= {day_range[0]}").query(f"day <= {day_range[1]}")
                print(f"\tafter filtering on {day_range[0]} <= day <= {day_range[1]}, we now have {len(df)} rows")
            elif query_key == "excluded_observers":
                excluded_observers = query_params[query_key]
                df = df.query(f"observer_code not in '{excluded_observers}'")
                print(f"\tafter filtering on observer_code not in '{excluded_observers}', we now have {len(df)} rows")
            else:
                value = query_params[query_key]
                if isinstance(value, str):
                    df = df.query(F"{query_key} == '{value}'")
                else:
                    df = df.query(F"{query_key} == {value}")
                print(f"\tafter filtering on {query_key} == {value}', we now have {len(df)} rows")

        print(f"\tand returning {len(df)} rows covering the bands/filters {df['band'].unique()}.")
        return df

    @abstractmethod
    def _on_query_magnitudes(self) -> DataFrame:
        """
        Implmented by subclass to return a DataFrame with standard magnitude field names
        """
        pass
