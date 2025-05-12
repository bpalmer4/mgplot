"""Package to provide a frontend to matplotlib."""

# from typing import Any

__version__ = "0.0.1"
__author__ = "Bryan Palmer"
__all__ = (
    "finalise_plot",
    "get_setting",
    "set_setting",
)
# __pdoc__: dict[str, Any] = {}  # hide submodules from documentation


# --- local imports
from mgplot.finalise_plot import finalise_plot
from mgplot.settings import get_setting, set_setting
