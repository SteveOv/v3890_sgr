from typing import Tuple, Any, Union
from pathlib import Path
import warnings
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from data.SpectralDataSource import *
from specutils import Spectrum1D, SpectrumCollection
from astropy import units
from data.SpectrumCollectionEx import SpectrumCollectionEx


class FrodoSpecSpectralDataSource(SpectralDataSource, ABC):
    """
    Data source for spectral data from the LT's FRODOspec instrument (in the form of fits files).
    This is set up as an abstract class.  It contains low level methods for reading spectral data while
    specifying the HDU and other parameters.  It is expected there will be concrete classes that derive
    from this that will wrap these methods to handle ingest/publishing data from specific HDUs.
    """

    @classmethod
    def read_spectra(cls, filename: Union[str, Path], hdu_name: str, selected_fibres: [] = None,
                     header: bool = False, label: str = None) \
            -> Union[SpectrumCollection, Tuple[Any, SpectrumCollectionEx]]:
        """
        Read the requested spectral data into a specutils SpectrumCollection.  If a fibre mask supplied
        only those spectra where the mask is true are returned, otherwise all spectra are returned.
        Returns the SpectrumCollection and optionally the HDU header.
        """
        data, hdr = fits.getdata(filename, hdu_name, header=True)
        hdr["CUNIT1"] = "Angstrom"          # It's actually "Angstroms" in the files

        # This decodes the headers which describe the spectral data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wcs = WCS(hdr)

        # Need to supply it with a spectral_axis it can work with
        # make index array - has to be the right size, as dictated by NAXIS1 x NAXIS2
        # from this the wcs (world coordinate system) can generate the wavelength axis.
        # Even then, it's not right for specutils and we have to transpose it before setting as the spectral axis!
        n_axis1 = hdr["NAXIS1"]
        n_axis2 = hdr["NAXIS2"]
        axis1 = np.arange(n_axis1)[:, np.newaxis]
        axis2 = np.arange(n_axis2)[np.newaxis, :]
        wavelengths = (wcs.wcs_pix2world(axis1, axis2, 0)[0]).transpose()

        if selected_fibres is None:
            flux = data * units.Unit("adu")
            spectral_axis = wavelengths * units.Unit("Angstrom")
        else:
            selection_mask = np.zeros(data.shape[0], dtype=bool)
            selection_mask.put(selected_fibres, True)
            flux = data[selected_fibres] * units.Unit("adu")
            spectral_axis = wavelengths[selected_fibres] * units.Unit("Angstrom")

        spectra = SpectrumCollectionEx(flux=flux, spectral_axis=spectral_axis, wcs=wcs, label=label)
        if header:
            return spectra, hdr
        else:
            return spectra

    @classmethod
    def read_spectrum(cls, filename: Union[str, Path], hdu_name: str, fibre: int = 0, header: bool = False) \
            -> Union[Spectrum1D, Tuple[Spectrum1D, Any]]:
        """
        Read the requested spectral data into a specutils Spectrum1D.  The fibre is used to specify
        which member to return if the HDU contains multiple spectra (defaults to zero).
        Returns the SpectrumCollection and optionally the HDU header.
        """
        spectra, hdr = cls.read_spectra(filename, hdu_name, [fibre], header=True)
        spectrum = spectra[0, :]
        if header:
            return spectrum, hdr
        else:
            return spectrum
