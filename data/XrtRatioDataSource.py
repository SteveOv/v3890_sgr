import re
from io import StringIO
import pandas as pd
from data.RateDataSource import *


class XrtRatioDataSource(RateDataSource):
    """
    Read and parse Xrt Hard/Soft-Ray Light Curve/Ratio Data files into 3 pandas DataFrames
    """

    def __init__(self, source: str):
        super().__init__(source)
        return

    def query_rates(self, eruption_jd, query_params: Dict, set_params: Dict = None) -> DataFrame:
        """
        """
        if "data_type" in query_params:
            df = self._on_query_rates().query(F"data_type in '{query_params['data_type']}'")
        else:
            df = self._on_query_rates()

        # We create day and log(day) field, relative to passed eruption jd
        df['day'] = np.subtract(np.add(df['jd'], 2400000), eruption_jd)
        df['day_err'] = df['jd_plus_err']

        # Now apply any query filters
        for query_key in query_params:
            if query_key == "day_range":
                day_range = query_params[query_key]
                df = df.query(f"day >= {day_range[0]}").query(f"day <= {day_range[1]}")
                print(f"\tafter filtering on {day_range[0]} <= day <= {day_range[1]}, we now have {len(df)} rows")

                # TODO: temp - filter on count regimes where the two approaches are stronger
                df = df.query("(rate_type == 'WT' and rate >= 1.0) or (rate_type == 'PC') and rate_err < rate")

        # If set_params supplied look for a filter value an then apply that
        if set_params is not None and "filter" in set_params:
            set_filter = set_params["filter"]
            df = df.query(F"{set_filter}")

        return df[["jd", "day", "day_err", "rate", "rate_err", "rate_type"]]

    def _on_query_rates(self) -> DataFrame:
        return self._df.query("rate_err == rate_err").query("rate_err > 0")

    def _ingest(self, source: str) -> (DataFrame, DataFrame, DataFrame):
        """
        Ingest the data from the specified source and return it as a pandas DataFrame
        Implements the abstract method in DataSource which is used to set up this instance's state.
        """
        # Have to pre-parse the file because of the "! WT data" and "! PC data" lines which delimit the two different
        # types of data.  We filter out these rows, and others which start with !, and instead use them to generate
        # an additional column at the start of each row from which the data can be ingested into a DataFrame.
        pattern = re.compile(r"!\s*([A-Za-z]*)\s*--\s*(soft data|hard data|hardness ratio)")
        csv = StringIO()
        with open(source, "r") as f:
            rate_type = None
            data_type = None
            for line in f:
                if line.strip().startswith("!"):
                    # OK, it's a header, comment or metadata line.
                    # We need to parse it first in case it tells us we are about to start a new subset
                    match = pattern.search(line)
                    if match is not None:
                        rate_type = match.group(1)
                        data_type = match.group(2).replace("data", "").replace("hardness", "").strip()
                elif data_type is not None and rate_type is not None:
                    csv.write(F"'{rate_type}'\t'{data_type}'\t{line}")

        csv.seek(0)
        df = pd.read_csv(csv,
                         header=0, delimiter="\t", index_col=None, comment="!", skip_blank_lines=True, quotechar="'")
        csv.close()
        df.columns = ["rate_type", "data_type", "jd", "jd_plus_err", "jd_minus_err", "rate", "rate_err", "obs_id"]
        return df
