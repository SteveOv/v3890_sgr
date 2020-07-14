import re
from io import StringIO
import pandas as pd
from data.RateDataSource import *


class XrtRateDataSource(RateDataSource):
    """
    Read and parse Xrt (Detailed) Light Curve Data files into pandas DataFrames
    """

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

        # TODO: temporary - add better handling - perhaps the larger absolute value
        df["rate_err"] = df["rate_plus_err"]

        # For these data there is no underlying "data_type" field,
        # but the rates are an aggregation of both hard and soft x-ray sources
        df["data_type"] = "both"
        return df


