from data.FrodoSpecSpectralDataSource import *


class CalibratedSpectralDataSource(FrodoSpecSpectralDataSource):
    """
    DataSource for calibrated spectral data held in the Primary HDU of a fits file.
    """
    @property
    def header(self):
        return self._header

    def _ingest(self, source: str) -> Union[DataFrame, Spectrum1DEx]:
        flux_scale_factor = self._kwargs["flux_scale_factor"] if "flux_scale_factor" in self._kwargs else 1
        spectrum, hdr = self.__class__.read_spectrum(source, header=True, flux_scale_factor=flux_scale_factor)
        self._header = hdr
        return spectrum

    def _on_query(self) -> Spectrum1DEx:
        return self._data.copy()
