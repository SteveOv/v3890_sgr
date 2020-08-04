import warnings
from typing import List, Type
import numpy as np
from specutils import SpectrumCollection, Spectrum1D
from astropy.units import Quantity
from data.spectrum.Spectrum1DEx import Spectrum1DEx


class SpectrumCollectionEx(SpectrumCollection):
    """
    Extends specutils SpectrumCollection to add support for spawning
    new collections based on a spectrum mask orlist of indices.
    """
    def __init__(self, flux: Quantity, spectral_axis=None, wcs=None, uncertainty=None,
                 mask=None, meta=None, label: str = "Unnamed"):
        super().__init__(flux, spectral_axis, wcs, uncertainty, mask, meta)
        self.label = label
        return

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    def __getitem__(self, key):
        """
        Gets the requested Spectrum.
        """
        # super().__getitem__() has been hard coded to return Spectrum1D so I've had to repro its functionality.
        flux = self.flux[key]
        if flux.ndim != 1:
            raise ValueError("Currently only 1D data structures may be returned from slice operations.")
        spectral_axis = self.spectral_axis[key]
        uncertainty = None if self.uncertainty is None else self.uncertainty[key]
        wcs = None if self.wcs is None else self.wcs[key]
        mask = None if self.mask is None else self.mask[key]
        if self.meta is None:
            meta = None
        else:
            try:
                meta = self.meta[key]
            except KeyError:
                meta = self.meta
        return Spectrum1DEx(flux=flux, spectral_axis=spectral_axis, uncertainty=uncertainty,
                            wcs=wcs, mask=mask, meta=meta)

    def copy_by_spectrum_mask(self, mask: [bool], label: str = None) -> Type["SpectrumCollectionEx"]:
        """
        Spawns a new SpectrumCollectionEx with copies of the spectra in this collection which match the passed mask
        """
        selections = np.where(mask)[0]
        return self.copy_by_indices(selections, label)

    def copy_by_indices(self, selections: List[int], label: str = None) -> Type["SpectrumCollectionEx"]:
        """
        Spawns a new SpectrumCollectionEx with copies of the spectra in this collection which match the passed indices.
        """
        new_label = label if label is not None else self.label
        name = self.__class__.__name__
        print(f"\tNew {name}('{new_label}') containing {selections} from {name}('{self.label}')")
        selected_spectra = []
        for ix in selections:
            selected_spectra.append(self[ix].copy())
        return self.__class__._from_spectra_list(selected_spectra, new_label)

    @classmethod
    def from_spectra(cls, spectra: List[Spectrum1D], label: str = "Unnamed"):
        print(f"\tNew {cls.__name__}('{label}') from list (length = {len(spectra)}).")
        return cls._from_spectra_list(spectra, label)

    @classmethod
    def _from_spectra_list(cls, spectra: List[Spectrum1D], label: str):
        # Doesn't work - still get the highly annoying warnings as they are to do with logging!
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            new_col = super().from_spectra(spectra)
            new_col.label = label
        return new_col

    def __repr__(self):
        return super().__repr__().replace("Collection(", f"CollectionEx(label='{self.label}', ")
