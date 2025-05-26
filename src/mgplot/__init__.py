"""Package to provide a frontend to matplotlib."""

# --- local imports
#    Do not import the utilities, test nor type-checking modules here.
from mgplot.finalise_plot import finalise_plot
from mgplot.bar_plot import bar_plot
from mgplot.line_plot import line_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.postcovid_plot import postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import run_plot
from mgplot.summary_plot import summary_plot
from mgplot.growth_plot import (
    calc_growth,
    raw_growth_plot,
    series_growth_plot,
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
)


# --- version and author
__version__ = "0.0.1"
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
    # --- The rest are internal use only
)
# __pdoc__: dict[str, Any] = {"test": False}  # hide submodules from documentation
