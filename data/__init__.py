from data.DataSource import *

"""
The Photometry data source hierarchy

                DataSource
                    ^
                    |
            PhotometryDataSource
            ^                   ^
            |                   |
    RateDataSource      MagnitudeDataSource         
            ^                   ^
            |                   |
    XrtRateDateSource       AavsoMagnitudeDataSource
    XrtRatioDataSource      SchaeferPhotometryDataSource
                            UvotFitsPhotometryDataSource
"""
from data.PhotometryDataSource import *

from data.MagnitudeDataSource import *
from data.RateDataSource import *

from data.AavsoMagnitudeDataSource import *
from data.SchaeferMagnitudeDataSource import *
from data.UvotMagnitudeDataSource import *

from data.XrtRateDataSource import *
from data.XrtRatioDataSource import *

"""
The Spectral data source hierarchy

                DataSource
                    ^
                    |
            SpectralDataSource
                    ^
                    |
            FrodoSpecSpectralDataSource
"""
from data.SpectralDataSource import *
from data.FrodoSpecSpectralDataSource import *
