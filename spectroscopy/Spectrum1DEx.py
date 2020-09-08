import warnings
import datetime
from typing import List, Union
import numpy as np
from specutils import Spectrum1D
from astropy.io import fits
from astropy.units import Quantity
from astropy.utils.exceptions import AstropyUserWarning
from specutils import SpectralRegion
from specutils.manipulation import noise_region_uncertainty

CRED = '\033[91m'
CGREEN = '\33[32m'
CBLUE = '\33[34m'
CEND = '\033[0m'


class Spectrum1DEx(Spectrum1D):
    """
    Extends specutils Spectrum1D.  Supports generating fits HDU from the spectral data.
    """
    def __init__(self, flux=None, spectral_axis=None, wcs=None, velocity_convention=None,
                 rest_value=None, redshift=None, radial_velocity=None, **kwargs):
        # Have to pop these as the base class will error for any unknown kwargs
        self._name = kwargs.pop("name") if "name" in kwargs else None
        self._mjd = kwargs.pop("mjd") if "mjd" in kwargs else None
        self._obs_date = kwargs.pop("obs_date") if "obs_date" in kwargs else None

        super().__init__(flux=flux, spectral_axis=spectral_axis, wcs=wcs, velocity_convention=velocity_convention,
                         rest_value=rest_value, redshift=redshift, radial_velocity=radial_velocity, **kwargs)
        return

    @property
    def min_wavelength(self) -> Quantity:
        return Quantity(min(self.wavelength.value), unit=self.wavelength.unit)

    @property
    def max_wavelength(self) -> Quantity:
        return Quantity(max(self.wavelength.value), unit=self.wavelength.unit)

    @property
    def max_flux(self) -> Quantity:
        return Quantity(max(self.flux.value), unit=self.flux.unit)

    @property
    def min_flux(self) -> Quantity:
        return Quantity(min(self.flux.value), unit=self.flux.unit)

    @property
    def is_blue(self) -> bool:
        return min(self.wavelength.value) < 5000

    @property
    def name(self) -> str:
        return self._name

    @property
    def mjd(self) -> float:
        return self._mjd

    @property
    def obs_date(self) -> datetime:
        return self._obs_date

    @classmethod
    def from_spectrum1d(cls, spec1d: Spectrum1D, name: str = None, mjd: float = None, obs_date: datetime = None):
        """
        Creates a instance of a Spectrum1DEx from the passed Spectrum1D
        """
        if spec1d is not None:
            new_spec = Spectrum1DEx(flux=spec1d.flux, spectral_axis=spec1d.spectral_axis,
                                    uncertainty=spec1d.uncertainty, wcs=spec1d.wcs, mask=spec1d.mask, meta=spec1d.meta)
            if isinstance(spec1d, Spectrum1DEx):
                new_spec._name = spec1d._name
                new_spec._mjd = spec1d._mjd
                new_spec._obs_date = spec1d._mjd

            if name is not None:
                new_spec._name = name

            if mjd is not None:
                new_spec._mjd = mjd

            if obs_date is not None:
                new_spec._obs_date = obs_date
        else:
            new_spec = None
        return new_spec

    @classmethod
    def spectral_region_centred_on(cls, lambda_c: float, width_ms: float, units: str = "Angstrom") \
            -> SpectralRegion:
        delta = (width_ms/2.998e8) * lambda_c
        return cls.spectral_region_over(lambda_c - delta, lambda_c + delta, units)

    @classmethod
    def spectral_region_over(cls, lambda_from: float, lambda_to: float, units: str = "Angstrom") \
            -> SpectralRegion:
        return SpectralRegion(Quantity(lambda_from, units), Quantity(lambda_to, units))

    @classmethod
    def spectral_regions_from_list(cls, lambda_list: Union[List[List[float]], List[float]], units: str = "Angstrom") \
            -> List[SpectralRegion]:
        if np.ndim(lambda_list) == 1:
            region_list = cls.spectral_regions_from_list([lambda_list], units)
        else:
            region_list = []
            for item in lambda_list:
                if len(item) == 2:
                    region_list.append(cls.spectral_region_over(min(item), max(item), units))
        return region_list

    def __getitem__(self, item):
        value = super().__getitem__(item)
        if isinstance(value, Spectrum1DEx):
            value._name = self._name
            value._mjd = self._mjd
            value._obs_date = self._obs_date
        return value

    def copy(self):
        """
        Create a copy of this spectrum
        """
        copy = super()._copy()
        copy._name = self._name
        copy._mjd = self._mjd
        copy._obs_date = self._obs_date
        return copy

    def to_uncertainty_spectrum(self, noise_region: SpectralRegion = None, new_name: str = None):
        """
        Derive the uncertainties in the spectrum from the noise. We use this for fitting as it provides weighting.
        The noise_region may be set to a region of the spectrum to base the uncertainty on (otherwise the whole is used).
        """
        if self.uncertainty is None:
            if noise_region is None:
                noise_region = self.spectral_region_over(self.min_wavelength.value, self.max_wavelength.value,
                                                         self.wavelength.unit)

            unc_spec = noise_region_uncertainty(self, noise_region)
            ret_val = Spectrum1DEx.from_spectrum1d(unc_spec, self._name, self._mjd, self._obs_date)
        else:
            ret_val = self.copy()

        if new_name is not None:
            ret_val._name = new_name

        return ret_val

    def create_image_hdu(self, name, header=None) \
            -> fits.ImageHDU:
        """
        Generate an ImageHDU from the data in this instance for saving to a fits file.
        """
        # TODO: need to set up the header better.  Will probably need a WCS to do this.
        if header is None:
            # Generate a new header for this
            header = fits.header

        # Make sure that the data is shaped correctly for the fits file.  It seems to work best with a 2nd axis.
        data = self.flux.value.copy()
        if len(data.shape) == 1:
            data = data[np.newaxis, :]

        header['NAXIS1'] = data.shape[0]
        header['NAXIS2'] = data.shape[1]
        header["NAXIS"] = 2
        header["EXTNAME"] = name
        return fits.ImageHDU(data=data, header=header, name=name)

    def detect_spikes(self, candidate_threshold: float = 100, falloff_fraction: float = 0.75, check_offset: float = 3) \
            -> List[SpectralRegion]:

        # Candidates are threshold X mean(of whole spectrum) (simple algorithm for now - maybe look at localised mean)
        mean_flux = np.mean(self.flux)
        flux_threshold = candidate_threshold * mean_flux  # candidate_threshold must not have units or we get adu2
        candidates = np.where(self.flux >= flux_threshold)[0]
        spikes = []

        ix_last_flux_to_check = len(self.flux) - check_offset - 1
        for c_ix in candidates:
            if (c_ix + 1) in candidates:
                # If its neighbour is in the list then it can't be a spike
                pass
            elif check_offset <= c_ix <= ix_last_flux_to_check:
                # A spike must have a precipitous fall in non_ss_spectra either side
                # (by default, losing > 0.75 non_ss_spectra either side)
                previous_flux = self.flux[c_ix - check_offset]
                next_flux = self.flux[c_ix + check_offset]
                this_flux = self.flux[c_ix]
                falloff = this_flux - ((this_flux - mean_flux) * falloff_fraction)
                if falloff > previous_flux and falloff > next_flux:
                    lambda_from = self.wavelength[c_ix - check_offset]
                    lambda_to = self.wavelength[c_ix + check_offset]
                    spikes.append(
                        SpectralRegion(lambda_from, lambda_to))
        return spikes

    def remove_spikes(self, spikes: List[SpectralRegion]):
        if spikes is not None:
            for spike in spikes:
                self._linear_interpolation_exciser(spike)
        return

    def _linear_interpolation_exciser(self, region: SpectralRegion):
        """
        This is a copy of the specutils' linear_exciser function with bug fixes so that it actually works.
        """
        # Don't take copies - we're going to do this in place
        spectral_axis = self.spectral_axis
        flux = self.flux
        if self.uncertainty is not None:
            new_uncertainty = self.uncertainty
        else:
            new_uncertainty = None

        # Need to add a check that the subregions don't overlap, since that could
        # cause undesired results. For now warn if there is more than one subregion
        if len(region) > 1:
            # Raise a warning if the SpectralRegion has more than one subregion, since
            # the handling for this is perhaps unexpected
            warnings.warn("A SpectralRegion with multiple subregions was provided as "
                          "input. This may lead to undesired behavior with _linear_interpolation_exciser if "
                          "the subregions overlap.",
                          AstropyUserWarning)

        for subregion in region:
            # Find the indices of the spectral_axis array corresponding to the subregion
            region_mask = (spectral_axis >= subregion.lower) & (spectral_axis < subregion.upper)
            inclusive_indices = np.nonzero(region_mask)[0]

            # Now set the flux values for these indices to be a linear range
            s, e = max(inclusive_indices[0]-1, 0), min(inclusive_indices[-1]+1, spectral_axis.size-1)

            # Fixed the bug here, where the specutils code's call to linspace generates Quantity with underlying value
            # array of float64, which when written to the modified_flux (float32) causes a loss of precision error!!!
            # new_flux = np.linspace(flux[s], flux[e], modified_flux[s: e + 1].size)
            new_flux = np.linspace(flux[s].value, flux[e].value, flux[s:e+1].size, dtype=flux.dtype.type)
            old_flux = flux[s:e+1]
            print(f"\tLinear interpolation({subregion.lower}, {subregion.upper}); replacing {CBLUE}{np.round(old_flux, 1)}{CEND} with {CGREEN}{np.round(new_flux, 1)}{CEND}")
            flux[s:e+1] = Quantity(new_flux, flux.unit)

            # Add the uncertainty of the two linear interpolation endpoints in
            # quadrature and apply to the excised region.
            if new_uncertainty is not None:
                new_uncertainty[s:e] = np.sqrt(self.uncertainty[s]**2 + self.uncertainty[e]**2)
        return

    def __repr__(self) \
            -> str:
        return super().__repr__().replace("Spectrum1D (", f"Spectrum1DEx (name='{self.name}', ")

    def __str__(self) \
            -> str:
        return super().__str__().replace("Spectrum1D (", f"Spectrum1DEx (name='{self.name}', ")
