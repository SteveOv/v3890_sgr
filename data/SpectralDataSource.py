from data.DataSource import *
from data.spectrum import *


class SpectralDataSource(DataSource, ABC):

    def query(self) -> Spectrum1DEx:
        """
        Query the data to get the required data
        """
        # Get a copy of the basic data set from the subclass
        spectrum = self._on_query()

        # Nothing to query yet
        return spectrum

    @abstractmethod
    def _on_query(self) -> Spectrum1DEx:
        """
        Called to get a data set for querying and returning to the client.
        Should fix up the data with time fields relative to the passed eruption JD.
        """
        pass
