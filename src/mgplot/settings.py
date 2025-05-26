"""
settings.py
This module provides a mechanosm for managing global settings.
"""

# --- imports
from typing import TypedDict, TypeVar, Any
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from pandas import Series, DataFrame


# --- default types
DataT = TypeVar("DataT", Series, DataFrame)  # python 3.11+


# --- global settings
plt.style.use("fivethirtyeight")
mpl.rcParams["font.size"] = 11


# --- default settings
class _DefaultValues(TypedDict):
    """
    _DefaultValues is a dictionary of default values for the settings.
    It is a TypedDict, which means that it knows a fixed set of keys
    and their corresponding types.
    """

    file_type: str
    figsize: tuple[float, float]
    file_dpi: int

    line_narrow: float
    line_normal: float
    line_wide: float

    bar_width: float

    legend_font_size: float | str
    legend: dict[str, Any]

    colors: dict[int, list[str]]  # used by get_color_list()

    chart_dir: str


_mgplot_defaults = _DefaultValues(
    file_type="png",
    figsize=(9.0, 4.5),
    file_dpi=300,
    line_narrow=0.75,
    line_normal=1.0,
    line_wide=2.0,
    bar_width=0.8,
    legend_font_size="small",
    legend={
        "loc": "best",
        "fontsize": "x-small",
    },
    colors={
        1: ["#dd0000"],
        5: ["royalblue", "darkorange", "forestgreen", "#dd0000", "gray"],
        9: [
            "darkblue",
            "darkorange",
            "forestgreen",
            "#dd0000",
            "purple",
            "gold",
            "lightcoral",
            "lightseagreen",
            "gray",
        ],
    },
    chart_dir=".",
)


# --- get/change settings


def get_setting(setting: str) -> Any:
    """
    Get a setting from the global settings.

    Arguments:
    - setting: str - name of the setting to get. The possible settings are:
        - file_type: str - the file type to use for saving plots
        - figsize: tuple[float, float] - the figure size to use for plots
        - file_dpi: int - the DPI to use for saving plots
        - line_narrow: float - the line width for narrow lines
        - line_normal: float - the line width for normal lines
        - line_wide: float - the line width for wide lines
        - bar_width: float - the width of bars in bar plots
        - legend_font_size: float | str - the font size for legends
        - legend: dict[str, Any] - the legend settings
        - colors: dict[int, list[str]] - a dictionary of colors for
          different numbers of lines
        - chart_dir: str - the directory to save charts in

    Raises:
        - KeyError: if the setting is not found

    Returns:
        - value: Any - the value of the setting
    """
    if setting not in _mgplot_defaults:
        raise KeyError(f"Setting '{setting}' not found in _mgplot_defaults.")
    return _mgplot_defaults[setting]  # type: ignore[literal-required]


def set_setting(setting: str, value: Any) -> None:
    """
    Set a setting in the global settings.
    Raises KeyError if the setting is not found.

    Arguments:
        - setting: str - name of the setting to set (see get_setting())
        - value: Any - the value to set the setting to
    """

    if setting not in _mgplot_defaults:
        raise KeyError(f"Setting '{setting}' not found in _mgplot_defaults.")
    _mgplot_defaults[setting] = value  # type: ignore[literal-required]


def clear_chart_dir() -> None:
    """
    Remove all graph-image files from the global chart_dir.
    This is a convenience function to remove all files from the
    chart_dir directory. It does not remove the directory itself.
    Note: the function creates the directory if it does not exist.
    """

    chart_dir = get_setting("chart_dir")
    Path(chart_dir).mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "jpg", "jpeg"):
        for fs_object in Path(chart_dir).glob(f"*.{ext}"):
            if fs_object.is_file():
                fs_object.unlink()


def set_chart_dir(chart_dir: str) -> None:
    """
    A function to set a global chart directory for finalise_plot(),
    so that it does not need to be included as an argument in each
    call to finalise_plot(). Create the directory if it does not exist.

    Note: Path.mkdir() may raise an exception if a directory cannot be created.

    Note: This is a wrapper for set_setting() to set the chart_dir setting, and
    create the directory if it does not exist.

    Arguments:
        - chart_dir: str - the directory to set as the chart directory
    """

    if not chart_dir:
        chart_dir = "."  # avoid the empty string
    Path(chart_dir).mkdir(parents=True, exist_ok=True)
    set_setting("chart_dir", chart_dir)
