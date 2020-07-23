from data.DataSource import *


class PhotometryDataSource(DataSource, ABC):

    def query(self, eruption_jd, query_params: Dict, set_params: Dict) -> DataFrame:
        """
        Query the data to get the required data
        """
        # Get the basic data set from the subclass
        df = self._on_query(eruption_jd)

        # Now apply any query filters
        if query_params is not None:
            for query_key in query_params:
                query_value = query_params[query_key]

                if query_key == "where":
                    # Generic filter/query expression in the form (where) "field == value"
                    df = df.query(query_value)
                    print(f"\tafter querying (query_params) : '{query_value}', {len(df)} rows left")

                elif query_key == "day_range":
                    d_range = query_params[query_key]
                    df = df.query(f"day >= {d_range[0]}").query(f"day <= {d_range[1]}")
                    print(f"\tafter querying (query_params) : {d_range[0]} <= day <= {d_range[1]}, {len(df)} rows left")

                elif query_key == "excluded_observers":
                    df = df.query(f"observer_code not in '{query_value}'")
                    print(f"\tafter query (query_params): observer_code not in '{query_value}', {len(df)} rows left")

                else:
                    if isinstance(query_value, str):
                        df = df.query(F"{query_key} == '{query_value}'")
                    else:
                        df = df.query(F"{query_key} == {query_value}")
                    print(f"\tafter query (query_params): {query_key} == '{query_value}', {len(df)} rows left")

        # If set_params supplied look for a where value and then apply that
        if set_params is not None and "where" in set_params:
            query_value = set_params["where"]
            df = df.query(query_value)
            print(f"\tafter querying (set_params): '{query_value}', {len(df)} rows left")

        # return whatever is left
        return df

    @abstractmethod
    def _on_query(self, eruption_jd: float) -> DataFrame:
        """
        Called to get a data set for querying and returning to the client.
        Should fix up the data with time fields relative to the passed eruption JD.
        """
        pass
