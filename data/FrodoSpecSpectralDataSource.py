from typing import List, Tuple, Any
import warnings
import numpy as np
from numpy import ndarray
from astropy.io import fits
from astropy.wcs import WCS
from data.SpectralDataSource import *


class FrodoSpecSpectralDataSource(SpectralDataSource, ABC):
    """
    Data source for spectral data from the LT's FRODOspec instrument (in the form of fits files).
    This is set up as an abstract class.  It contains low level methods for reading spectral data while
    specifying the HDU and other parameters.  It is expected there will be concrete classes that derive
    from this that will wrap these methods to handle ingest/publishing data from specific HDUs.
    """

    @classmethod
    def read_spec_into_arrays(cls, filename: str, hdu_name: str) -> Tuple[Any, ndarray, ndarray]:
        """
        Read the requested spectral data into separate arrays for wavelength and flux.
        Returns the HDU header, wavelength ndarray, spectra ndarray
        """
        sp = fits.open(filename)
        header = sp[hdu_name].header
        n_axis1 = header["NAXIS1"]
        n_axis2 = header["NAXIS2"]

        # This decodes the headers which describe the spectral data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wcs = WCS(header)

        # make index array - has to be the right size, as dictated by NAXIS1 x NAXIS2
        # from this the wcs (world coordinate system) can generate the wavelength axis.
        axis1 = np.arange(n_axis1)[:, np.newaxis]
        axis2 = np.arange(n_axis2)[np.newaxis, :]
        wavelength = wcs.wcs_pix2world(axis1, axis2, 0)

        flux = sp[hdu_name].data

        # Convert wavelength column vector[0] into the same form as the flux data
        wavelength = wavelength[0].transpose()
        return header, wavelength, flux

    @classmethod
    def read_spec_into_long_list(cls, filename: str, hdu_name: str) -> Tuple[Any, List]:
        """
        Read the requested spectral data into a single "long" List[int, float, float] with columns
            spec
            wavelength
            flux
        Returns HDU header and the list
        """
        header, wavelength, flux = cls.read_spec_into_arrays(filename, hdu_name)
        rows = []
        wavelength_ixs = np.arange(flux.shape[1])
        for spec_ix in np.arange(flux.shape[0]):
            for wavelength_ix in wavelength_ixs:
                rows.append([spec_ix, wavelength[spec_ix, wavelength_ix], flux[spec_ix, wavelength_ix]])

        return header, rows

    @classmethod
    def read_spec_into_long_dataframe(cls, filename: str, hdu_name: str) -> Tuple[Any, DataFrame]:
        """
        Read the requested spectral data into a single pandas DataFrame with columns
            spec
            wavelength
            flux
        Returns HDU header and the DataFrame (indexed on spec and wavelength)
        """
        header, rows = cls.read_spec_into_long_list(filename, hdu_name)
        df = DataFrame.from_records(rows, columns=["spec", "wavelength", "flux"])
        return header, df
