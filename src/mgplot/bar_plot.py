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
from mgplot.utilities import (
    apply_defaults,
    get_color_list,
    get_axes,
    constrain_data,
    default_rounding,
)
from mgplot.kw_type_checking import (
    ExpectedTypeDict,
    validate_expected,
    report_kwargs,
    validate_kwargs,
)
from mgplot.axis_utils import set_labels, map_periodindex, is_categorical


# --- constants
# - plot and data constants
AXES = "ax"  # used to control the axes to plot on
DROPNA = "dropna"  # used to control dropping NaN values
STACKED = "stacked"  # used to control if the bars are stacked or grouped
ROTATION = "rotation"  # used to control the rotation of x-axis labels
MAX_TICKS = "max_ticks"  # used to control the maximum number of ticks on the x-axis
PLOT_FROM = "plot_from"  # used to control the starting point of the plot
# - bar plot constants
LEGEND = "legend"  # used to control the legend display
COLOR = "color"  # used to control the color of the bars
WIDTH = "width"  # used to control the width of the bars
LABEL_SERIES = "label_series"  # used to control the labeling of series in the legend
# - annoptation constants
ANNOTATE = "annotate"  # used to control the annotation of bars
FONTSIZE = "fontsize"  # used to control the font size of annotations
FONTNAME = "fontname"  # used to control the font name of annotations
BAR_ROTATION = "bar_rotation"  # used to control the rotation of bar labels
ANNO_COLOR = "annotate_color"  # used to control the color of annotations
ROUNDING = "rounding"  # used to control the rounding of annotations
ABOVE = "above"  # used to control the position of annotations

BAR_KW_TYPES: Final[ExpectedTypeDict] = {
    # --- options for the entire bar plot
    AXES: (Axes, type(None)),  # axes to plot on, or None for new axes
    STACKED: bool,  # if True, the bars will be stacked. If False, they will be grouped.
    ROTATION: (int, float),  # rotation of x-axis labels in degrees
    MAX_TICKS: int,
    PLOT_FROM: (int, PeriodIndex, type(None)),
    LEGEND: (bool, dict, (str, object), type(None)),
    # --- options for each bar ...
    COLOR: (str, Sequence, (str,)),
    LABEL_SERIES: (bool, Sequence, (bool,)),
    WIDTH: (float, Sequence, (float,)),
    # - options for bar annotations
    ANNOTATE: (type(None), bool),  # None, True
    FONTSIZE: (int, float, str),
    FONTNAME: (str),
    BAR_ROTATION: (int, float),  # rotation of bar labels
    ROUNDING: int,
    ANNO_COLOR: (str, type(None)),  # color of annotations
    ABOVE: bool,  # if True, annotations are above the bar
    # - other bar attributes
}
validate_expected(BAR_KW_TYPES, "bar_plot")


# --- functions
def annotate_bars(
    series: Series,
    offset: float,
    base: np.ndarray[tuple[int, ...], np.dtype[Any]],
    axes: Axes,
    **kwargs,
) -> None:
    """Bar plot annotations."""

    # --- only annotate in limited circumstances
    if ANNOTATE not in kwargs or kwargs[ANNOTATE] is None or kwargs[ANNOTATE] is False:
        return
    max_annotations = 30
    if len(series) > max_annotations:
        return

    # --- internal logic check
    if len(base) != len(series):
        print(
            f"Warning: base array length {len(base)} does not match series length {len(series)}."
        )
        return

    # --- assemble the annotation parameters
    above: Final[bool | None] = kwargs.get(ABOVE, False)  # None is also False-ish
    annotate_style = {
        "fontsize": kwargs.get(FONTSIZE),
        "fontname": kwargs.get(FONTNAME),
        "color": kwargs.get(ANNO_COLOR),
        "rotation": kwargs.get(BAR_ROTATION),
    }
    rounding = default_rounding(series=series, provided=kwargs.get(ROUNDING, None))
    adjustment = (series.max() - series.min()) * 0.01
    rebase = series.index.min()

    # --- annotate each bar
    for index, value in zip(series.index.astype(int), series):  # mypy syntactic sugar
        position = base[index - rebase] + (adjustment if value >= 0 else -adjustment)
        if above:
            position += value
        text = axes.text(
            x=index + offset,
            y=position,
            s=f"{value:.{rounding}f}",
            ha="center",
            va="bottom" if value >= 0 else "top",
            **annotate_style,
        )
        if not above and "foreground" in kwargs:
            # apply a stroke-effect to within bar annotations
            # to make them more readable with very small bars.
            text.set_path_effects(
                [pe.withStroke(linewidth=2, foreground=kwargs.get("foreground"))]
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
        adjusted_width = width / series_count  # 0.8
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
        annotate_bars(
            series,
            offset,
            np.zeros(len(series)),
            axes,
            foreground=foreground,
            **anno_args,
        )


def stacked(axes, df: DataFrame, anno_args, **kwargs) -> None:
    """
    plot a stacked bar plot
    """

    series_count = len(df)
    base_plus: np.ndarray[tuple[int, ...], np.dtype[np.float64]] = np.zeros(
        shape=series_count, dtype=np.float64
    )
    base_minus: np.ndarray[tuple[int, ...], np.dtype[np.float64]] = np.zeros(
        shape=series_count, dtype=np.float64
    )
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
        annotate_bars(series, 0, base, axes, foreground=foreground, **anno_args)
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
        /* affects the entire bar plot */
        - ax: Axes | None - The axes to plot on. If None, a new figure and axes will be created.
        - stacked: bool - If True, the bars will be stacked. If False, they will be grouped.
        - rotation: int | float - The rotation of the x-axis labels in degrees.
        - max_ticks: int - The maximum number of ticks on the x-axis (for PeriodIndex only)
        - plot_from: int | PeriodIndex | None - The starting point of the plot.
          If None, the entire data will be plotted.
        - legend: bool | dict | (str, object) | None - If True, a legend will be created.
        /* affects the bars in the bar plot */
        - color: str | Sequence[str] - The color of the bars. If a sequence is provided,
          it should match the number of columns in the DataFrame.
        - label_series: bool | Sequence[bool] - If True, the series will be labeled in
          the legend. If a sequence is provided, it should match the number of columns
          in the DataFrame.
        /* options for bar annotations */
        - annotate: None | bool - If True, the bars will be annotated with their values.
        - fontsize: int | float | str - The font size of the annotations.
        - fontname: str - The font name of the annotations.
        - bar_rotation: int | float - The rotation of the bar labels in degrees.
        - rounding: int | bool - The number of decimal places to round the annotations.
          If True, a default between 0 and 2 is used.
        - annotate_color: str - The color of the annotations.
        - above: bool - If True, the annotations will be placed above the bars.

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
        ANNOTATE: kwargs.get(ANNOTATE, False),
        FONTSIZE: kwargs.get(FONTSIZE, "small"),
        FONTNAME: kwargs.get(FONTNAME, "Helvetica"),
        BAR_ROTATION: kwargs.get(BAR_ROTATION, 0),
        ROUNDING: kwargs.get(ROUNDING, True),
        ANNO_COLOR: kwargs.get(ANNO_COLOR, "white"),
        ABOVE: kwargs.get(ABOVE, False),
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, bar_defaults, kwargs)
    chart_defaults: dict[str, Any] = {
        STACKED: False,
        ROTATION: 90,
        MAX_TICKS: 10,
        LEGEND: item_count > 1,
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
