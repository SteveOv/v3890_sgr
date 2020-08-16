from typing import Dict


class MetadataDict(Dict):
    """
    Specialized dictionary which supports bulk updates via conflate and returning default values where items missing.
    """

    def __init__(self, source: Dict = None, **kwargs):
        super().__init__(**kwargs)
        self.conflate(source)
        return

    def conflate(self, new_values: Dict):
        """
        Apply the passed new values to this dictionary replacing existing or creating new entries as needed.
        """
        if new_values is not None:
            for k, v in new_values.items():
                self[k] = v
        return

    def get_or_default(self, key, default=None):
        """
        Get the requested value (by its key) or return the supplied default value if it doesn't exist.
        """
        return super().get(key) if key in self.keys() else default

    def has_key(self, key) -> bool:
        return key in self.keys()
