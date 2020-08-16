from abc import ABC
from utility.MetadataDict import *


class WithMetadata(ABC):

    def __init__(self, **kwargs):
        self._metadata = MetadataDict(source=kwargs)
        return

    @property
    def metadata(self) -> MetadataDict:
        return self._metadata
