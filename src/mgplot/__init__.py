"""Package to provide a frontend to matplotlib."""

# from typing import Any

__version__ = "0.0.1"
__author__ = "Bryan Palmer"
__all__ = (
    "__version__",
    "__author__",
    # settings
    "get_setting",
    "set_setting",
    "set_chart_dir",
    "clear_chart_dir",
    # finalise_plot
    "finalise_plot",
    "get_finalise_kwargs_list",
    # line_plot
    "line_plot",
    "line_plot_finalise",
    "line_plot_multistart",
    "seas_trend_plot",
    # growth plot
)
# __pdoc__: dict[str, Any] = {}  # hide submodules from documentation


# --- local imports
from mgplot.finalise_plot import finalise_plot, get_finalise_kwargs_list
from mgplot.settings import get_setting, set_setting, set_chart_dir, clear_chart_dir
from mgplot.line_plot import (
    line_plot,
    line_plot_finalise,
    line_plot_multistart,
    seas_trend_plot,
)
