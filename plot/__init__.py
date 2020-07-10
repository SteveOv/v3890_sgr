from plot.BasePlot import *
from plot.PlotHelper import *

# These both inherit directly from BasePlot.
# They have multiple axes, so may look to create a MultiplePlot intermediate parent class.
from plot.RatesAndRatioTimePlot import *
from plot.TwoByTwoMagnitudeLogTimePlot import *

# These are all based on a new hierarchy, with SinglePlot inheriting BasePlot and the rest descending from SinglePlot
from plot.SinglePlot import *
from plot.SinglePlotSupportingLogAxes import *
from plot.SingleMagnitudeTimePlot import *
from plot.MagnitudeFitResidualsTimePlot import *
from plot.SingleRateTimePlot import *
from plot.SingleMagnitudeAndRateTimePlot import *

from plot.SpectralEvolutionDistributionPlot import *
from plot.ColorMagnitudePlot import *
