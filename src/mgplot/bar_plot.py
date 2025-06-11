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
from pandas import Series, DataFrame, Period
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes
import matplotlib.patheffects as pe


from mgplot.settings import DataT, get_setting
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
from mgplot.keyword_names import (
    AX,
    STACKED,
    ROTATION,
    MAX_TICKS,
    PLOT_FROM,
    COLOR,
    LABEL_SERIES,
    WIDTH,
    ANNOTATE,
    FONTSIZE,
    FONTNAME,
    ROUNDING,
    ANNOTATE_COLOR,
    ABOVE,
)


# --- constants

BAR_KW_TYPES: Final[ExpectedTypeDict] = {
    # --- options for the entire bar plot
    AX: (Axes, type(None)),  # axes to plot on, or None for new axes
    STACKED: bool,  # if True, the bars will be stacked. If False, they will be grouped.
    MAX_TICKS: int,
    PLOT_FROM: (int, Period, type(None)),
    # --- options for each bar ...
    COLOR: (str, Sequence, (str,)),
    LABEL_SERIES: (bool, Sequence, (bool,)),
    WIDTH: (float, int),
    # - options for bar annotations
    ANNOTATE: (type(None), bool),  # None, True
    FONTSIZE: (int, float, str),
    FONTNAME: (str),
    ROUNDING: int,
    ROTATION: (int, float),  # rotation of annotations in degrees
    ANNOTATE_COLOR: (str, type(None)),  # color of annotations
    ABOVE: bool,  # if True, annotations are above the bar
}
validate_expected(BAR_KW_TYPES, "bar_plot")


# --- functions
def annotate_bars(
    series: Series,
    offset: float,
    base: np.ndarray[tuple[int, ...], np.dtype[Any]],
    axes: Axes,
    **anno_kwargs,
) -> None:
    """Bar plot annotations.

    Note: "annotate", "fontsize", "fontname", "color", and "rotation" are expected in anno_kwargs.
    """

    # --- only annotate in limited circumstances
    if ANNOTATE not in anno_kwargs or not anno_kwargs[ANNOTATE]:
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
    above: Final[bool | None] = anno_kwargs.get(ABOVE, False)  # None is also False-ish
    annotate_style = {
        FONTSIZE: anno_kwargs.get(FONTSIZE),
        FONTNAME: anno_kwargs.get(FONTNAME),
        COLOR: anno_kwargs.get(COLOR),
        ROTATION: anno_kwargs.get(ROTATION),
    }
    rounding = default_rounding(series=series, provided=anno_kwargs.get(ROUNDING, None))
    adjustment = (series.max() - series.min()) * 0.02
    zero_correction = series.index.min()

    # --- annotate each bar
    for index, value in zip(series.index.astype(int), series):  # mypy syntactic sugar
        position = base[index - zero_correction] + (
            adjustment if value >= 0 else -adjustment
        )
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
        if not above and "foreground" in anno_kwargs:
            # apply a stroke-effect to within bar annotations
            # to make them more readable with very small bars.
            text.set_path_effects(
                [pe.withStroke(linewidth=2, foreground=anno_kwargs.get("foreground"))]
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
            label=col if kwargs[LABEL_SERIES][i] else f"_{col}_",
        )
        annotate_bars(
            series=series,
            offset=offset,
            base=np.zeros(len(series)),
            axes=axes,
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
            width=kwargs[WIDTH][i],
            label=col if kwargs[LABEL_SERIES][i] else f"_{col}_",
        )
        annotate_bars(
            series=series,
            offset=0,
            base=base,
            axes=axes,
            foreground=foreground,
            **anno_args,
        )
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
    # --- options for the entire bar plot
    ax: Axes - axes to plot on, or None for new axes
    stacked: bool - if True, the bars will be stacked. If False, they will be grouped.
    max_ticks: int - maximum number of ticks on the x-axis (for PeriodIndex only)
    plot_from: int | PeriodIndex - if provided, the plot will start from this index.
    # --- options for each bar ...
    color: str | list[str] - the color of the bars (or separate colors for each series
    label_series: bool | list[bool] - if True, the series will be labeled in the legend
    width: float | list[float] - the width of the bars
    # - options for bar annotations
    annotate: bool - If True them annotate the bars with their values.
    fontsize: int | float | str - font size of the annotations
    fontname: str - font name of the annotations
    rounding: int - number of decimal places to round to
    annotate_color: str  - color of annotations
    rotation: int | float - rotation of annotations in degrees
    above: bool - if True, annotations are above the bar, else within the bar

    Note: This function does not assume all data is timeseries with a PeriodIndex,

    Returns
    - axes: Axes - The axes for the plot.
    """

    # --- check the kwargs
    me = "bar_plot"
    report_kwargs(called_from=me, **kwargs)
    kwargs = validate_kwargs(BAR_KW_TYPES, me, **kwargs)

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
    chart_defaults: dict[str, Any] = {
        STACKED: False,
        MAX_TICKS: 10,
        LABEL_SERIES: item_count > 1,
    }
    chart_args = {k: kwargs.get(k, v) for k, v in chart_defaults.items()}

    bar_defaults: dict[str, Any] = {
        COLOR: get_color_list(item_count),
        WIDTH: get_setting("bar_width"),
        LABEL_SERIES: (item_count > 1),
    }
    above = kwargs.get(ABOVE, False)
    anno_args = {
        ANNOTATE: kwargs.get(ANNOTATE, False),
        FONTSIZE: kwargs.get(FONTSIZE, "small"),
        FONTNAME: kwargs.get(FONTNAME, "Helvetica"),
        ROTATION: kwargs.get(ROTATION, 0),
        ROUNDING: kwargs.get(ROUNDING, True),
        COLOR: kwargs.get(ANNOTATE_COLOR, "black" if above else "white"),
        ABOVE: above,
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, bar_defaults, kwargs)

    # --- plot the data
    axes, _rkwargs = get_axes(**remaining_kwargs)
    if chart_args[STACKED]:
        stacked(axes, df, anno_args, **bar_args)
    else:
        grouped(axes, df, anno_args, **bar_args)

    # --- handle complete periodIndex data and label rotation
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], chart_args["max_ticks"])
    else:
        plt.xticks(rotation=90)

    return axes
