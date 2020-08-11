from plot.PlotData import *
from plot.BasePlot import *


class TimePlot(BasePlot, ABC):
    """
    Produces a data vs time plot for 1+ sets of data on a single axis, optionally overlaying with fitted lines.
    The following plot params are supported (in addition to the standard params defined by BasePlot);
        * show_data (True) - plot the raw data
        * show_fits (False) - draw the line fits
        * show_epochs / show_epoch_labels (False/False) - controls drawing of epoch lines & labels on x-axis
        * y_shift (0) - optional shift in the y-axis for each subsequent data_set
    For each PlotSet the following rate_params are supported:
        * color
        * label
    """

    def __init__(self, plot_params: Dict):
        super().__init__(plot_params)

        self._default_show_data = True
        self._default_show_fits = False
        self._default_show_epochs = False
        self._default_show_epoch_labels = False

        self._default_y_shift = 0
        return

    @property
    def show_data(self) -> bool:
        return self._param("show_data", self._default_show_data)

    @property
    def show_fits(self) -> bool:
        return self._param("show_fits", self._default_show_fits)

    @property
    def show_epochs(self) -> bool:
        return self._param("show_epochs", self._default_show_epochs)

    @property
    def show_epoch_labels(self) -> bool:
        return self._param("show_epoch_labels", self._default_show_epoch_labels)

    @property
    def y_shift(self) -> float:
        return self._param("y_shift", self._default_y_shift)

    def _draw_plot_data(self, ax: Axes, **kwargs):
        """
        Override of the BasePlot abstract method where we actually get to draw data onto the Axes.
        """
        plot_data = kwargs["plot_data"]

        # Potential hooks for the subtype to plot each data type
        self._draw_plot_sets(ax, plot_data.plot_sets)

        # Potential hook for subtype to choose whether/how to render epoch data
        if self.show_epochs:
            self._draw_epochs(ax, plot_data.epochs)
        return

    def _draw_plot_sets(self, ax: Axes, plot_sets: Dict[str, PlotSet]):
        if plot_sets is not None:
            ix = 0
            for set_key in plot_sets.keys():
                ps = plot_sets[set_key]
                self._draw_plot_set(ax, ix, ps)
                ix += 1
        return

    def _draw_plot_set(self, ax: Axes, ix: int, ps: PlotSet):
        this_y_shift = self.y_shift * ix
        label = self._define_data_label(ps.label, this_y_shift)
        color = ps.color

        # Render the base data
        if self.show_data:
            self._plot_points_to_error_bars_on_ax(ax, x_points=ps.x, y_points=ps.y, y_err_points=ps.y_err,
                                                  color=color, label=label, y_shift=this_y_shift)

        # Optionally draw any fitted lines
        if self.show_fits and ps.fits is not None:
            if self.show_data:
                label = None    # Already associated the label with data, so don't need to do so here
            ps.fits.draw_on_ax(ax, color, label=label, line_width=self._line_width, y_shift=this_y_shift)
        return

    def _draw_epochs(self, ax: Axes, epochs: Dict[str, float]):
        if epochs is not None and len(epochs) > 0:
            # Replace the minor x-axis ticks with the epochs specified.
            ax.set_xticks(list(epochs.values()), minor=True)
            ax.set_xticklabels(list(epochs.keys()) if self.show_epoch_labels else [], minor=True)

            # Labels, if shown, are rotated 90deg and within the axis.
            ax.tick_params(which='minor', axis='x', direction='inout', pad=-25, labelsize='x-small',
                           labelcolor='gray', labelrotation=90)
            ax.grid(which='minor', linestyle=':', linewidth=self._line_width, alpha=0.2)
        return

    def _define_data_label(self, label: str, shift_by: float = 0) -> str:
        return label + (F" (shifted {shift_by:+.1f})" if shift_by != 0 else "")