from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type, Union
from pandas import DataFrame
from data.spectrum import *


class DataSource(ABC):
    """
    Base class for the photometry data source classes
    """
    _subclasses = None

    def __init__(self, source: str, **kwargs):
        print(F"\n{self.__class__.__name__}: Ingesting/parsing data from '{source}' ...")

        # Store any extended arguments - base doesn't know of them but subclass may do.
        self._kwargs = kwargs

        self._data = self._ingest(source)
        if isinstance(self._data, DataFrame):
            print(F"\t... ingested {len(self._data)} row(s).")
        elif isinstance(self._data, Spectrum1DEx):
            print(F"\t... ingested {self._data.flux.shape[0]} spectral readings over {self._data.spectral_axis}.")
        return

    @classmethod
    def create(cls, type_name: str, source: str, **kwargs) -> Type["DataSource"]:
        """
        Factory method for creating a DataSource of the chosen type with the requested source.
        Will raise a KeyError if the type_name is not a recognised subclass.
        """
        ctor = cls._get_subclass_hierarchy()[type_name.casefold()]
        data_source = ctor(source, **kwargs)
        return data_source

    @classmethod
    def create_from_config(cls, config: Dict, default_type_name: str = None) -> Type["DataSource"]:
        if "type" in config:
            type_name = config["type"]
        elif default_type_name is not None:
            type_name = default_type_name
        else:
            raise KeyError("No type specified")

        if "file_spec" in config:
            source = config["file_spec"]
        elif "source" in config:
            source = config["source"]
            config.pop("source")        # remove this to prevent clash with specific, named argument.
        else:
            raise KeyError("No source specified")

        # Pass the rest of the config dictionary on as **kwargs
        return cls.create(type_name, source, **config)

    @abstractmethod
    def _ingest(self, source: str) -> Union[DataFrame, Spectrum1DEx]:
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

    @classmethod
    def _canonicalize_filename(cls, filename: Union[str, Path]) -> Path:
        if isinstance(filename, str):
            filename = Path(filename)
        filename = filename.expanduser()
        if not filename.is_absolute():
            filename = filename.resolve()
        return filename
