from typing import Dict, List
from pandas import DataFrame
from fitting import FitSet


class PlotSet:
    """
    The data and configuration driving the plotting of a single set of data (eg: band or filter)
    """

    def __init__(self, name: str, df: DataFrame, params: Dict, fits: FitSet = None):
        self.__name = name
        self.__df = df
        self.__params = params
        self.__fits = fits

        # column names - only needed while we base underlying data on a DataFrame
        self.__x_col = self.param("x_col", "day")
        self.__x_err_col = self.param("x_err_col", None)
        self.__y_col = self.param("y_col", "mag")
        self.__y_err_col = self.param("y_err_col", "mag_err")
        self.__data_type = "rate" if self.__y_col == "rate" else "band"
        return

    def __str__(self):
        return F"{self.__class__.__name__}: {self.__name}"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def data_type(self) -> str:
        return self.__data_type

    @property
    def x(self) -> List[float]:
        return self.__df[self.__x_col].to_list()

    @property
    def x_err(self) -> List[float]:
        return self.__df[self.__x_err_col].to_list() if self.__x_err_col is not None else None

    @property
    def y(self) -> List[float]:
        return self.__df[self.__y_col].to_list()

    @property
    def y_err(self) -> List[float]:
        return self.__df[self.__y_err_col].to_list() if self.__y_err_col is not None else None

    @property
    def df(self) -> DataFrame:
        # TODO: drop this when possible.  Don't want clients to have to deal with data frames
        return self.__df.copy()

    @property
    def fits(self) -> FitSet:
        return self.__fits

    @property
    def label(self) -> str:
        return self.param("label", self.__name)

    @property
    def color(self) -> str:
        return self.param("color", "k")

    def param(self, key, default=None):
        return self.__params[key] if self.has_param(key) else default

    def has_param(self, key):
        return key in self.__params
