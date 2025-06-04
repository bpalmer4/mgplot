"""
bar_plot.py
This module contains functions to create bar plots using Matplotlib.
Note: bar plots in Matplotlib are not the same as bar charts in other
libraries. Bar plots are used to represent categorical data with
rectangular bars. As a result, bar plots and line plots typically
cannot be plotted on the same axes.
"""

# --- imports
from typing import Any, Final
from collections.abc import Sequence

import numpy as np
from pandas import Series, DataFrame, PeriodIndex
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes
import matplotlib.patheffects as pe


from mgplot.settings import DataT, get_setting
from mgplot.finalise_plot import make_legend
from mgplot.utilities import apply_defaults, get_color_list, get_axes, constrain_data
from mgplot.kw_type_checking import (
    ExpectedTypeDict,
    validate_expected,
    report_kwargs,
    validate_kwargs,
)
from mgplot.axis_utils import set_labels, map_periodindex, is_categorical


# --- constants
LEGEND = "legend"  # used to control the legend display
ANNOTATE = "annotate"  # used to control the annotation of bars
FONTSIZE = "fontsize"  # used to control the font size of annotations
FONTNAME = "fontname"  # used to control the font name of annotations
BAR_ROTATION = "bar_rotation"  # used to control the rotation of bar labels
ANNO_COLOR = "annotate_color"  # used to control the color of annotations
ROUNDING = "rounding"  # used to control the rounding of annotations

BAR_KW_TYPES: Final[ExpectedTypeDict] = {
    # --- options for each bar ...
    "color": (str, Sequence, (str,)),
    "label_series": (bool, Sequence, (bool,)),
    "width": (float, Sequence, (float,)),
    # --- options for the entire bar plot
    ANNOTATE: (type(None), bool),  # None, True
    FONTSIZE: (int, float, str),
    FONTNAME: (str),
    BAR_ROTATION: (int, float),  # rotation of bar labels
    ROUNDING: int,
    ANNO_COLOR: str,  # color of annotations
    "stacked": bool,
    "rotation": (int, float),
    "max_ticks": int,
    "plot_from": (int, PeriodIndex, type(None)),
    LEGEND: (bool, dict, (str, object), type(None)),
}
validate_expected(BAR_KW_TYPES, "bar_plot")


# --- functions
def annotated(
    series: Series,
    offset: float,
    base: np.ndarray[float],
    axes: Axes,
    **kwargs,
) -> None:
    """Bar plot annotations."""


    # --- only annotate in limited circumstances
    max_annotations = 30
    if len(series) > max_annotations:
        return
    if len(base) != len(series):
        print(
            f"Warning: base array length {len(base)} does not match series length {len(series)}."
        )
        return

    # --- annotate each bar
    annotate = kwargs.get(ANNOTATE, None)
    if annotate is None or annotate is False:
        return

    # --- get the annotation styles
    annotate_style = {
        "fontsize": kwargs.get(FONTSIZE, "small"),
        "fontname": kwargs.get(FONTNAME, "Helvetica"),
        "color": kwargs.get(ANNO_COLOR, "white"),
        "rotation": kwargs.get(BAR_ROTATION, 0),
    }
    rounding = kwargs.get(
        ROUNDING,
        0 if series.max() >= 100 else 1 if series.max() >= 10 else 2
    )

    adjustment = (series.max() - series.min()) * 0.01

    rebase = series.index.min()
    for index, value in series.items():
        va = "bottom" if value >= 0 else "top"
        text = axes.text(
            index + offset,
            base[index - rebase] + (adjustment if value >= 0 else -adjustment),
            f"{value:.{rounding}f}",
            ha="center",
            va=va,
            **annotate_style,
        )
        text.set_path_effects(
            [pe.withStroke(linewidth=2, foreground=kwargs.get("foreground", "black"))]
        )


def grouped(axes, df: DataFrame, anno_args, **kwargs) -> None:
    """
    plot a grouped bar plot
    """

    series_count = len(df.columns)

    for i, col in enumerate(df.columns):
        series = df[col]
        if series.isnull().all():
            continue
        width = kwargs["width"][i]
        if width < 0 or width > 1:
            width = 0.8
        adjusted_width = width / series_count   # 0.8
        # far-left + margin + halfway through one grouped column
        left = -0.5 + ((1 - width) / 2.0) + (adjusted_width / 2.0)
        offset = left + (i * adjusted_width)
        foreground = kwargs["color"][i]
        axes.bar(
            x=series.index + offset,
            height=series,
            color=foreground,
            width=adjusted_width,
            label=col if kwargs["label_series"][i] else "_not_in_legend_",
        )
        annotated(
            series, offset, np.zeros(len(series)), axes, foreground=foreground, **anno_args
        )


def stacked(axes, df: DataFrame, anno_args, **kwargs) -> None:
    """
    plot a stacked bar plot
    """

    series_count = len(df)
    base_plus = np.zeros(series_count, dtype=float)
    base_minus = np.zeros(series_count, dtype=float)
    for i, col in enumerate(df.columns):
        series = df[col]
        base = np.where(series >= 0, base_plus, base_minus)
        foreground = kwargs["color"][i]
        axes.bar(
            x=series.index,
            height=series,
            bottom=base,
            color=foreground,
            width=kwargs["width"][i],
            label=col if kwargs["label_series"][i] else "_not_in_legend_",
        )
        annotated(series, 0, base, axes, foreground=foreground, **anno_args)
        base_plus += np.where(series >= 0, series, 0)
        base_minus += np.where(series < 0, series, 0)


def bar_plot(
    data: DataT,
    **kwargs,
) -> Axes:
    """
    Create a bar plot from the given data. Each column in the DataFrame
    will be stacked on top of each other, with positive values above
    zero and negative values below zero.

    Parameters
    - data: Series - The data to plot. Can be a DataFrame or a Series.
    - **kwargs: dict Additional keyword arguments for customization.
        - color: list - A list of colors for the each series (column) in  the DataFrame.
        - width: float - The width of the bars.
        - stacked: bool - If True, the bars will be stacked.
        - rotation: int - The rotation angle in degrees for the x-axis labels.
        - label_series: bool - If True, label this series. Defaults to True
          if more than one bar being plotted for each category.
        = legend - bool | dict - If True, display a legend.
          If a dict, it will be passed to the legend function.
        - "max_ticks": int - The maximum number of ticks on the x-axis,
          (this option only applies to PeriodIndex data.).

    Note: This function does not assume all data is timeseries with a PeriodIndex,

    Returns
    - axes: Axes - The axes for the plot.
    """

    # --- check the kwargs
    me = "bar_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(BAR_KW_TYPES, me, **kwargs)

    # --- get the data
    # no call to check_clean_timeseries here, as bar plots are not
    # necessarily timeseries data. If the data is a Series, it will be
    # converted to a DataFrame with a single column.
    df = DataFrame(data)  # really we are only plotting DataFrames
    df, kwargs = constrain_data(df, **kwargs)
    item_count = len(df.columns)

    # --- deal with complete PeriodIdex indicies
    if not is_categorical(df):
        print(
            "Warning: bar_plot is not designed for incomplete or non-categorical data indexes."
        )
    saved_pi = map_periodindex(df)
    if saved_pi is not None:
        df = saved_pi[0]  # extract the reindexed DataFrame from the PeriodIndex

    # --- set up the default arguments
    bar_defaults: dict[str, Any] = {
        "color": get_color_list(item_count),
        "width": get_setting("bar_width"),
        "label_series": (item_count > 1),
    }
    anno_args = {
        ANNOTATE: True,
        FONTSIZE: "x-small",
        FONTNAME: "Helvetica",
        BAR_ROTATION: 0,
        ROUNDING: 1,
        ANNO_COLOR: "white",
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, bar_defaults, kwargs)
    chart_defaults: dict[str, Any] = {
        "stacked": False,
        "rotation": 90,
        "max_ticks": 10,
        "LEGEND": item_count > 1,
    }
    chart_args = {k: kwargs.get(k, v) for k, v in chart_defaults.items()}

    # --- plot the data
    axes, _rkwargs = get_axes(**remaining_kwargs)
    if chart_args["stacked"]:
        stacked(axes, df, anno_args, **bar_args)
    else:
        grouped(axes, df, anno_args, **bar_args)

    # --- handle complete periodIndex data and label rotation
    rotate_labels = True
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], chart_args["max_ticks"])
        rotate_labels = False

    if rotate_labels:
        plt.xticks(rotation=chart_args["rotation"])

    # --- add a legend if requested
    if "LEGEND" in chart_args:
        make_legend(axes, chart_args["LEGEND"])

    return axes
