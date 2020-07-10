from abc import ABC, abstractmethod
from typing import Dict, Type
from pandas import DataFrame


class DataSource(ABC):
    """
    Base class for the photometry data source classes
    """

    _subclasses = None

    def __init__(self, source: str):
        print(F"\n{self.__class__.__name__}: Ingesting/parsing data from '{source}' ...")
        self._df = self._ingest(source)
        print(F"\t... ingested {len(self._df)} row(s).")
        return

    @classmethod
    def create(cls, type_name: str, source: str) -> Type["DataSource"]:
        """
        Factory method for creating a DataSource of the chosen type with the requested source.
        Will raise a KeyError if the type_name is not a recognised subclass.
        """
        ctor = cls._get_subclass_hierarchy()[type_name.casefold()]
        data_source = ctor(source)
        return data_source

    @abstractmethod
    def _ingest(self, source: str) -> DataFrame:
        """
        Ingest the data from the specified source and return it as a pandas DataFrame.
        """
        pass

    @classmethod
    def _read_from_params(cls, key: str, params: Dict, default):
        return params[key] if key in params else default

    @classmethod
    def _get_subclass_hierarchy(cls):
        """
        Gets all the subclasses descending the class hierarchy.
        Use instead of __subclasses__() which appears to only get immediate subclasses.
        """
        if cls._subclasses is None:
            cls._subclasses = cls._get_subclasses()
        return cls._subclasses

    @classmethod
    def _get_subclasses(cls):
        sc_dict = {}
        subclasses = cls.__subclasses__()
        for subclass in subclasses:
            sc_dict[subclass.__name__.casefold()] = subclass
            if issubclass(subclass, DataSource):
                sc_dict.update(subclass._get_subclasses())
        return sc_dict
