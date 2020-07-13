import re
from io import StringIO
import pandas as pd
from data.RateDataSource import *


class XrtRateDataSource(RateDataSource):
    """
    Read and parse Xrt (Detailed) Light Curve Data files into pandas DataFrames
    """

    def query_rates(self, eruption_jd, query_params: Dict = None, set_params: Dict = None) -> DataFrame:
        """
        """
        df = self._on_query_rates().copy()

        # We create day and log(day) field, relative to passed eruption jd
        df['day'] = np.subtract(np.add(df['jd'], 2400000), eruption_jd)
        df['day_err'] = df['jd_plus_err']

        # TODO: temp
        df['rate_err'] = df['rate_plus_err']

        # Now apply any query filters
        if query_params is not None:
            for query_key in query_params:
                if query_key == "day_range":
                    day_range = query_params[query_key]
                    df = df.query(f"day >= {day_range[0]}").query(f"day <= {day_range[1]}")
                    print(f"\tafter filtering on {day_range[0]} <= day <= {day_range[1]}, we now have {len(df)} rows")

        # If set_params supplied look for a filter value an then apply that
        if set_params is not None and "filter" in set_params:
            set_filter = set_params["filter"]
            df = df.query(f"{set_filter}")

        return df[["jd", "day", "day_err", "rate", "rate_err", "rate_type"]]

    def _on_query_rates(self) -> DataFrame:
        return self._df

    def _ingest(self, source: str) -> DataFrame:
        """
        Ingest the data from the specified source and return it as a pandas DataFrame
        Implements the abstract method in DataSource which is used to set up this instance's state.
        """
        # Have to pre-parse the file because of the "! WT data" and "! PC data" lines which delimit the two different
        # types of data.  We filter out these rows, and others which start with !, and instead use them to generate
        # an additional column at the start of each row from which the data can be ingested into a DataFrame.
        pattern = re.compile(r"\s*!\s*([A-Za-z]*)\s*data\s*$")
        csv = StringIO()
        with open(source, "r") as f:
            rate_type = None
            for line in f:
                if line.strip().startswith("!"):
                    # OK, it's a header, comment or metadata line. Parse it to see if it tells us we're in a new group
                    match = pattern.search(line)
                    if match is not None:
                        rate_type = match.group(1)
                elif rate_type is not None:
                    csv.write(F"'{rate_type}'\t{line}")

        csv.seek(0)
        file_column_names = ["rate_type", "jd", "jd_plus_err", "jd_minus_err", "rate", "rate_plus_err",
                             "rate_minus_err", "bg_rate", "bg_err", "frac_exp", "obs_id"]
        df = pd.read_csv(csv,
                         header=0, delimiter="\t", index_col=None, comment="!", skip_blank_lines=True, quotechar="'")
        df.columns = file_column_names
        return df
