import re
from io import StringIO
import pandas as pd
from data.RateDataSource import *


class XrtRatioDataSource(RateDataSource):
    """
    Read and parse Xrt Hard/Soft X-Ray Rate and Ratio Data files into 3 pandas DataFrames
    """

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
        source = self.__class__._canonicalize_filename(source)
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
                        # Leave the data_type as; hard, soft or ratio
                        data_type = match.group(2).replace("data", "").replace("hardness", "").strip()
                elif data_type is not None and rate_type is not None:
                    csv.write(F"'{rate_type}'\t'{data_type}'\t{line}")

        csv.seek(0)
        df = pd.read_csv(csv,
                         header=0, delimiter="\t", index_col=None, comment="!", skip_blank_lines=True, quotechar="'")
        csv.close()
        df.columns = ["rate_type", "data_type", "mjd", "mjd_plus_err", "mjd_minus_err", "rate", "rate_err", "obs_id"]
        return df

