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
        Read the requested spectral data into a SpectrumCollectionEx.  If a fibre mask supplied
        only those spectra where the mask is true are returned, otherwise all spectra are returned.
        Returns the SpectrumCollectionEx and optionally the HDU header.
        """
        data, hdr = fits.getdata(filename, hdu_name, header=True)
        hdr["CUNIT1"] = "Angstrom"          # It's actually "Angstroms" in the files

        # Check the data and wavelength shapes match NAXIS1/2.  Need to get this right otherwise creating the
        # wavelength/spectral_axis via the WCS or assigning it to SpecCollection fails (data/wavelengths must match)
        # For FRODO SPEC_SS:    NAXIS1 = #flux_readings, NAXIS2 = 1                     data={ndarray: (1, xxxx)}
        # For FRODO RSS_NONSS:  NAXIS1 = #flux_readings, NAXIS2 = fibre count (144)     data={ndarray: (144, xxxx)}
        # For some og my fits:  NAXIS1 = #flux_reasings, NAXIS2 = <missing>             data={ndarray: (xxxx,)}
        # For my SPEC_SS_MED:   NAXIS1 = #flux_readings, NAXIS2 = 1                     data={ndarray: (1, xxxx)}
        # Need to make sure we can cope with all of these! NAXIS1 = #flux/wavelength readings, NAXIS2 = #fibres/spectra
        n_axis1 = hdr["NAXIS1"]
        n_axis2 = hdr["NAXIS2"] if "NAXIS2" in hdr else None
        if n_axis2 is None and len(data.shape) == 1:
            # For some data written out NAXIS2 is missing and the data is in the form {ndarray: (xxxx,)}.
            # This can be made usable if we interpret NAXIS2 = 1 and reshape the data to match; {ndarray: (1, xxxx)}.
            hdr["NAXIS"] = 2
            n_axis2 = hdr["NAXIS2"] = 1
            data = data[np.newaxis, :]

        # This decodes the headers which describe the spectral data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wcs = WCS(hdr)

        # Need to supply it with a spectral_axis it can work with - has to be the right shape and size, as described by
        # NAXIS1 x NAXIS2. From this the wcs (world coordinate system) can generate the wavelength axis. Even then, it's
        # not right for specutils and we have to transpose it to match the data before setting as the spectral axis!
        axis1 = np.arange(n_axis1)[:, np.newaxis]
        axis2 = np.arange(n_axis2)[np.newaxis, :]
        spectral_axis = (wcs.wcs_pix2world(axis1, axis2, 0)[0]).transpose()

        # Now we should have both the data and wavelength data set up with the same size & shape.  Get them ready.
        assert data.shape == spectral_axis.shape
        if selected_fibres is None:
            flux = data * units.Unit("adu")
            spectral_axis = spectral_axis * units.Unit("Angstrom")
        else:
            selection_mask = np.zeros(data.shape[0], dtype=bool)
            selection_mask.put(selected_fibres, True)
            flux = data[selected_fibres] * units.Unit("adu")
            spectral_axis = spectral_axis[selected_fibres] * units.Unit("Angstrom")

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
        Returns the Spectrum1D and optionally the HDU header.
        """
        spectra, hdr = cls.read_spectra(filename, hdu_name, [fibre], header=True)
        spectrum = spectra[0, :]
        if header:
            return spectrum, hdr
        else:
            return spectrum
