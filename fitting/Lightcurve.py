from typing import List
from pandas import DataFrame
from utility import WithMetadata
from fitting import *
from data.DataSource import *


class Lightcurve(WithMetadata):

    def __init__(self, name: str, df: DataFrame, **kwargs):
        super().__init__(**kwargs)
        self._name = name
        self._df = df

        # column names - only needed while we base underlying data on a DataFrame
        self._x_col = self.metadata.get_or_default("x_col", "day")
        self._x_err_col = self.metadata.get_or_default("x_err_col", None)

        # Look for the columns that would be used for the y-data.  mag/mag_err for Vis/UV or rate/rate_err for X-ray
        if "mag" in df.columns:
            self._data_type = "mag"
            self._y_col = "mag"
            self._y_err_col = "mag_err"
        elif "rate" in df.columns:
            self._data_type = "rate"
            self._y_col = "rate"
            self._y_err_col = "rate_err"
        else:
            raise ValueError("Unknown data type.  Neither mag nor rate columns found")
        print(f"Lightcurve({name}): Initialized")
        return

    def __str__(self):
        return F"{self.__class__.__name__}: {self._name}"

    @property
    def name(self) -> str:
        return self._name

    @property
    def data_type(self) -> str:
        return self._data_type

    @property
    def x(self) -> List[float]:
        return self._df[self._x_col].to_list()

    @property
    def x_err(self) -> List[float]:
        return self._df[self._x_err_col].to_list() if self._x_err_col is not None else None

    @property
    def y(self) -> List[float]:
        return self._df[self._y_col].to_list()

    @property
    def y_err(self) -> List[float]:
        return self._df[self._y_err_col].to_list() if self._y_err_col is not None else None

    @property
    def df(self) -> DataFrame:
        # TODO: drop this when possible.  Don't want clients to have to deal with data frames directly
        return self._df.copy()

    @property
    def label(self) -> str:
        return self.metadata.get_or_default("label", self._name)

    @classmethod
    def create_from_data_source(cls, name: str, data_source: DataSource, grp_config: Dict):
        eruption_jd = grp_config["eruption_jd"]
        grp_query_params = grp_config["query_params"]
        lc_config = grp_config["lightcurves"][name]
        df = data_source.query(eruption_jd, grp_query_params, lc_config)
        return Lightcurve(name, df, **lc_config)
