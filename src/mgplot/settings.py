"""Managing global default settings."""

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, TypeVar

import matplotlib as mpl
import matplotlib.pyplot as plt
from pandas import DataFrame, Series

# --- default types
DataT = TypeVar("DataT", Series, DataFrame)  # python 3.11+


# --- global plot settings
plt.style.use("fivethirtyeight")
mpl.rcParams["font.size"] = 11


# --- default settings
@dataclass
class DefaultTypes:
    """Types for the global global settings of the mgplot module."""

    file_type: str
    figsize: tuple[float, float]
    dpi: int

    line_narrow: float
    line_normal: float
    line_wide: float

    bar_width: float

    legend_font_size: float | str
    legend: dict[str, Any]

    colors: dict[int, list[str]]  # used by get_color_list()

    chart_dir: str
    max_ticks: int  # default for x-axis ticks


mgplot_defaults = DefaultTypes(
    file_type="png",
    figsize=(9.0, 4.5),
    dpi=300,
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
        5: ["darkblue", "darkorange", "mediumseagreen", "#dd0000", "gray"],
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
    max_ticks=13,
)


# --- get/change settings


def get_fields() -> list[str]:
    """Get a list of field names in the global settings.

    Returns:
        list[str] - a list of field names in the global settings

    """
    return [a.name for a in fields(mgplot_defaults)]


def get_setting(setting: str) -> Any:
    """Get a setting from the global settings.

    Args:
        setting: str - name of the setting to get.

    Raises:
        KeyError: if the setting is not found

    Returns:
        value: Any - the value of the setting

    """
    if setting not in get_fields():
        raise KeyError(f"Setting '{setting}' not found in mgplot_defaults.")
    return getattr(mgplot_defaults, setting)


def set_setting(setting: str, value: Any) -> None:
    """Set a setting in the global settings.

    Args:
        setting: str - name of the setting to set (see get_setting())
        value: Any - the value to set the setting to

    """
    if setting not in get_fields():
        raise KeyError(f"Setting '{setting}' not found in mgplot_defaults.")
    setattr(mgplot_defaults, setting, value)


def clear_chart_dir() -> None:
    """Remove all graph-image files from the global chart_dir."""
    chart_dir = get_setting("chart_dir")
    Path(chart_dir).mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg", "jpg", "jpeg"):
        for fs_object in Path(chart_dir).glob(f"*.{ext}"):
            if fs_object.is_file():
                fs_object.unlink()


def set_chart_dir(chart_dir: str) -> None:
    """Set a global chart directory for finalise_plot().

    Args:
        chart_dir: str - the directory to set as the chart directory

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
