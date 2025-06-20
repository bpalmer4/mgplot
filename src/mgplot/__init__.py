"""mgplot
------

Package to provide a frontend to matplotlib for working
with timeseries data that is indexed with a PeriodIndex.
"""

# --- version and author
import importlib.metadata

# --- local imports
#    Do not import the utilities, axis_utils nor keyword_checking modules here.
from mgplot.bar_plot import BarKwargs, bar_plot
from mgplot.colors import (
    abbreviate_state,
    colorise_list,
    contrast,
    get_color,
    get_party_palette,
    state_abbrs,
    state_names,
)
from mgplot.finalise_plot import FinaliseKwargs, finalise_plot
from mgplot.finalisers import (
    bar_plot_finalise,
    growth_plot_finalise,
    line_plot_finalise,
    postcovid_plot_finalise,
    revision_plot_finalise,
    run_plot_finalise,
    seastrend_plot_finalise,
    series_growth_plot_finalise,
    summary_plot_finalise,
)
from mgplot.growth_plot import (
    GrowthKwargs,
    SeriesGrowthKwargs,
    calc_growth,
    growth_plot,
    series_growth_plot,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.multi_plot import multi_column, multi_start, plot_then_finalise
from mgplot.postcovid_plot import PostcovidKwargs, postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import RunKwargs, run_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.settings import (
    clear_chart_dir,
    get_setting,
    set_chart_dir,
    set_setting,
)
from mgplot.summary_plot import SummaryKwargs, summary_plot

# --- version and author
try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback for development mode
__author__ = "Bryan Palmer"


# --- public API
__all__ = (
    "__version__",
    "__author__",
    # --- settings
    "get_setting",
    "set_setting",
    "set_chart_dir",
    "clear_chart_dir",
    # --- colors
    "get_color",
    "get_party_palette",
    "colorise_list",
    "contrast",
    "abbreviate_state",
    "state_names",
    "state_abbrs",
    # --- bar plot
    "bar_plot",
    "BarKwargs",
    # --- line plot
    "line_plot",
    "LineKwargs",
    # --- seasonal + trend plot
    "seastrend_plot",
    # --- post-COVID plot
    "postcovid_plot",
    "PostcovidKwargs",
    # --- run plot
    "run_plot",
    "RunKwargs",
    # --- revision plot
    "revision_plot",
    # --- growth plot
    "growth_plot",
    "GrowthKwargs",
    "series_growth_plot",
    "SeriesGrowthKwargs",
    "calc_growth",
    # --- summary plot
    "summary_plot",
    "SummaryKwargs",
    # --- multi plot
    "multi_start",
    "multi_column",
    "plot_then_finalise",
    # --- finalise plot
    "finalise_plot",
    "FinaliseKwargs",
    # --- finalisers
    "bar_plot_finalise",
    "line_plot_finalise",
    "postcovid_plot_finalise",
    "growth_plot_finalise",
    "revision_plot_finalise",
    "run_plot_finalise",
    "seastrend_plot_finalise",
    "series_growth_plot_finalise",
    "summary_plot_finalise",
    # --- The rest are internal use only
)
# __pdoc__: dict[str, Any] = {"test": False}  # hide submodules from documentation
