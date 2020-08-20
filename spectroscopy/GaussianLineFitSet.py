from typing import Tuple, Union, Dict, Any
from matplotlib.axes import Axes
from specutils import SpectralRegion
from spectroscopy import *
from utility import WithMetadata


class GaussianLineFitSet(WithMetadata):

    def __init__(self, name: str, fits: List[GaussianLineFit], **kwargs):
        self._name = name
        self._fits = fits
        super().__init__(**kwargs)
        return

    def __iter__(self) -> [GaussianLineFit]:
        return self._fits.__iter__()

    def __next__(self) -> GaussianLineFit:
        return self._fits.__next__()

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> str:
        return self.metadata.get_or_default("label", self.name)

    @classmethod
    def fit_to_data(cls, name: str, spectrum: Spectrum1DEx,
                    noise_regions: Union[SpectralRegion, Dict[str, SpectralRegion]],
                    hints: Dict[str, Dict[str, Any]],
                    start_id: int = 0, **kwargs):
        line_fits = []

        # Can either be a single region to use for all fits, or a dictionary sharing keys
        has_master_region = isinstance(noise_regions, SpectralRegion)
        noise_region = noise_regions if has_master_region else None

        for label in hints:
            hint = hints[label]
            if not has_master_region:
                noise_region = noise_regions[label] if label in noise_regions else None

            line_fits.append(GaussianLineFit.fit_to_data(id=start_id, spectrum=spectrum, noise_region=noise_region,
                                                         hint=hint, label=label, **kwargs))
            start_id += 1

        fit_set = cls(name, line_fits, **kwargs)
        return fit_set

    def draw_on_ax(self, ax: Axes, line_width: float = 0.5,
                   label: str = None, y_shift: float = 0, annotate: bool = True):
        """
        Gets the FitSet to draw itself onto the passed matplotlib ax
        """
        for fit in self:
            fit.draw_on_ax(ax, line_width=line_width, label=label, y_shift=y_shift, annotate=annotate)
        return
