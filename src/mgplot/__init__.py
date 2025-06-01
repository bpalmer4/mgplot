"""
mgplot
------

Package to provide a frontend to matplotlib for working
with timeseries data that is indexed with a PeriodIndex.
"""

# --- version and author
import importlib.metadata

# --- local imports
#    Do not import the utilities, test nor type-checking modules here.
from mgplot.finalise_plot import finalise_plot, FINALISE_KW_TYPES
from mgplot.bar_plot import bar_plot, BAR_KW_TYPES
from mgplot.line_plot import line_plot, LINE_KW_TYPES
from mgplot.seastrend_plot import seastrend_plot, SEASTREND_KW_TYPES
from mgplot.postcovid_plot import postcovid_plot, POSTCOVID_KW_TYPES
from mgplot.revision_plot import revision_plot, REVISION_KW_TYPES
from mgplot.run_plot import run_plot, RUN_KW_TYPES
from mgplot.summary_plot import summary_plot, SUMMARY_KW_TYPES
from mgplot.growth_plot import (
    calc_growth,
    raw_growth_plot,
    series_growth_plot,
    SERIES_GROWTH_KW_TYPES,
    RAW_GROWTH_KW_TYPES,
)
from mgplot.multi_plot import (
    multi_start,
    multi_column,
    plot_then_finalise,
)
from mgplot.colors import (
    get_color,
    get_party_palette,
    colorise_list,
    contrast,
    abbreviate_state,
    state_names,
    state_abbrs,
)
from mgplot.settings import (
    get_setting,
    set_setting,
    set_chart_dir,
    clear_chart_dir,
)
from mgplot.finalisers import (
    line_plot_finalise,
    bar_plot_finalise,
    seastrend_plot_finalise,
    postcovid_plot_finalise,
    revision_plot_finalise,
    summary_plot_finalise,
    raw_growth_plot_finalise,
    series_growth_plot_finalise,
    run_plot_finalise,
)


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
    # --- finalise_plot
    "finalise_plot",
    # --- line_plot
    "line_plot",
    # --- bar plot
    "bar_plot",
    # --- seastrend_plot
    "seastrend_plot",
    # --- postcovid_plot
    "postcovid_plot",
    # --- revision_plot
    "revision_plot",
    # --- run_plot
    "run_plot",
    # --- summary_plot
    "summary_plot",
    # --- growth_plot
    "calc_growth",
    "raw_growth_plot",
    "series_growth_plot",
    # --- multi_plot
    "multi_start",
    "multi_column",
    "plot_then_finalise",
    # --- finaliser functions
    "line_plot_finalise",
    "bar_plot_finalise",
    "seastrend_plot_finalise",
    "postcovid_plot_finalise",
    "revision_plot_finalise",
    "summary_plot_finalise",
    "raw_growth_plot_finalise",
    "series_growth_plot_finalise",
    "run_plot_finalise",
    # --- typing information
    "FINALISE_KW_TYPES",
    "BAR_KW_TYPES",
    "LINE_KW_TYPES",
    "SEASTREND_KW_TYPES",
    "POSTCOVID_KW_TYPES",
    "REVISION_KW_TYPES",
    "RUN_KW_TYPES",
    "SUMMARY_KW_TYPES",
    "SERIES_GROWTH_KW_TYPES",
    "RAW_GROWTH_KW_TYPES",
    # --- The rest are internal use only
)
# __pdoc__: dict[str, Any] = {"test": False}  # hide submodules from documentation
