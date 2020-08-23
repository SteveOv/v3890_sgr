from typing import Union, List
from astropy.time import Time
import numpy as np

jd_mjd_offset = 2400000.5


def delta_t_from_jd(jd: Union[float, List[float]], reference_jd: float) -> Union[float, List[float]]:
    """
    Derive Delta-t value(s) as the difference between the passed jd and reference_jd values.
    """
    return np.subtract(jd, reference_jd)


def jd_from_mjd(mjd: Union[float, List[float]]) -> Union[float, List[float]]:
    """
    Derive the (JD) Julian Date(s) from the passed Modified Julian Date(s).
    """
    return np.add(mjd, jd_mjd_offset)


def mjd_from_jd(jd: Union[float, List[float]]) -> Union[float, List[float]]:
    """
    Derive the Modified Julian Data(s) from the passed Julian Date(s)
    """
    return np.subtract(jd, jd_mjd_offset)


def date_time_from_jd(jd, format: str = "isot"):
    time = Time(jd, format="jd")
    return time.to_value(format=format)
