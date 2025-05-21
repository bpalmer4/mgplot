"""Package to provide a frontend to matplotlib."""

# from typing import Any

__version__ = "0.0.1"
__author__ = "Bryan Palmer"
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
    "get_finalise_kwargs_list",
    # --- line_plot
    "line_plot",
    "line_plot_finalise",
    "seas_trend_plot",
    # --- growth plot
    "calc_growth",
    "growth_plot",
    "growth_plot_from_series",
    # --- bar plot
    "bar_plot",
    "bar_plot_finalise",
    # --- summary plot
    "summary_plot",
    # --- revision plot
    "revision_plot",
    # --- covid recovery plot
    "covid_recovery_plot",
    # --- multi_plot
    "multi_start",
    "multi_column",
    # Note: test and utilities are not public
)
# __pdoc__: dict[str, Any] = {"test": False}  # hide submodules from documentation


# --- local imports
#    Do not import the utilities, test nor type-checking modules here.
from mgplot.finalise_plot import finalise_plot, get_finalise_kwargs_list
from mgplot.growth_plot import calc_growth, growth_plot, growth_plot_from_series
from mgplot.bar_plot import bar_plot, bar_plot_finalise
from mgplot.summary_plot import summary_plot
from mgplot.revision_plot import revision_plot
from mgplot.covid_recovery_plot import covid_recovery_plot
from mgplot.multi_plot import multi_start, multi_column
from mgplot.colors import (
    get_color,
    get_party_palette,
    colorise_list,
    contrast,
    abbreviate_state,
    state_names,
    state_abbrs,
)
from mgplot.line_plot import (
    line_plot,
    line_plot_finalise,
    seas_trend_plot,
)
from mgplot.settings import (
    get_setting,
    set_setting,
    set_chart_dir,
    clear_chart_dir,
)
