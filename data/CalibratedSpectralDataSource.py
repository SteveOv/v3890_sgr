from data.FrodoSpecSpectralDataSource import *


class CalibratedSpectralDataSource(FrodoSpecSpectralDataSource):
    """
    DataSource for calibrated spectral data held in the Primary HDU of a fits file.
    """
    @property
    def header(self):
        return self._header

    def _ingest(self, source: str) -> Union[DataFrame, Spectrum1DEx]:
        spectrum, hdr = self.__class__.read_spectrum(source, header=True)
        self._header = hdr
        return spectrum

    def _on_query(self) -> Spectrum1DEx:
        return self._data.copy()
