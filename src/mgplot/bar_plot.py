"""Create bar plots using Matplotlib.

Note: bar plots in Matplotlib are not the same as bar charts in other
libraries. Bar plots are used to represent categorical data with
rectangular bars. As a result, bar plots and line plots typically
cannot be plotted on the same axes.
"""

from collections.abc import Sequence
from typing import Any, Final, NotRequired, Unpack

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.pyplot import Axes
from pandas import DataFrame, Period, Series

from mgplot.axis_utils import is_categorical, map_periodindex, set_labels
from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import DataT, get_setting
from mgplot.utilities import (
    apply_defaults,
    constrain_data,
    default_rounding,
    get_axes,
    get_color_list,
)

# --- constants
ME: Final[str] = "bar_plot"


class BarKwargs(BaseKwargs):
    """Keyword arguments for the bar_plot function."""

    # --- options for the entire bar plot
    ax: NotRequired[Axes | None]
    stacked: NotRequired[bool]
    max_ticks: NotRequired[int]
    plot_from: NotRequired[int | Period]
    # --- options for each bar ...
    color: NotRequired[str | Sequence[str]]
    label_series: NotRequired[bool | Sequence[bool]]
    width: NotRequired[float | int | Sequence[float | int]]
    # --- options for bar annotations
    annotate: NotRequired[bool]
    fontsize: NotRequired[int | float | str]
    fontname: NotRequired[str]
    rounding: NotRequired[int]
    rotation: NotRequired[int | float]
    annotate_color: NotRequired[str]
    above: NotRequired[bool]


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
    if "annotate" not in anno_kwargs or not anno_kwargs["annotate"]:
        return
    max_annotations = 30
    if len(series) > max_annotations:
        return

    # --- internal logic check
    if len(base) != len(series):
        print(f"Warning: base array length {len(base)} does not match series length {len(series)}.")
        return

    # --- assemble the annotation parameters
    above: Final[bool | None] = anno_kwargs.get("above", False)  # None is also False-ish
    annotate_style = {
        "fontsize": anno_kwargs.get("fontsize"),
        "fontname": anno_kwargs.get("fontname"),
        "color": anno_kwargs.get("color"),
        "rotation": anno_kwargs.get("rotation"),
    }
    rounding = default_rounding(series=series, provided=anno_kwargs.get("rounding"))
    adjustment = (series.max() - series.min()) * 0.02
    zero_correction = series.index.min()

    # --- annotate each bar
    for index, value in zip(series.index.astype(int), series, strict=False):  # mypy syntactic sugar
        position = base[index - zero_correction] + (adjustment if value >= 0 else -adjustment)
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
            text.set_path_effects([pe.withStroke(linewidth=2, foreground=anno_kwargs.get("foreground"))])


def grouped(axes: Axes, df: DataFrame, anno_args: dict[str, Any], **kwargs) -> None:
    """Plot a grouped bar plot."""
    series_count = len(df.columns)

    for i, col in enumerate(df.columns):
        series = df[col]
        if series.isna().all():
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
            label=col if kwargs["label_series"][i] else f"_{col}_",
        )
        annotate_bars(
            series=series,
            offset=offset,
            base=np.zeros(len(series)),
            axes=axes,
            foreground=foreground,
            **anno_args,
        )


def stacked(axes: Axes, df: DataFrame, anno_args: dict[str, Any], **kwargs) -> None:
    """Plot a stacked bar plot."""
    series_count = len(df)
    base_plus: np.ndarray[tuple[int, ...], np.dtype[np.float64]] = np.zeros(
        shape=series_count,
        dtype=np.float64,
    )
    base_minus: np.ndarray[tuple[int, ...], np.dtype[np.float64]] = np.zeros(
        shape=series_count,
        dtype=np.float64,
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
            label=col if kwargs["label_series"][i] else f"_{col}_",
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


def bar_plot(data: DataT, **kwargs: Unpack[BarKwargs]) -> Axes:
    """Create a bar plot from the given data.

    Each column in the DataFrame
    will be stacked on top of each other, with positive values above
    zero and negative values below zero.

    Args:
        data: Series - The data to plot. Can be a DataFrame or a Series.
        **kwargs: BarKwargs - Additional keyword arguments for customization.
        (see BarKwargs for details)

    Note: This function does not assume all data is timeseries with a PeriodIndex,

    Returns:
        axes: Axes - The axes for the plot.

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=BarKwargs, caller=ME, **kwargs)

    # --- get the data
    # no call to check_clean_timeseries here, as bar plots are not
    # necessarily timeseries data. If the data is a Series, it will be
    # converted to a DataFrame with a single column.
    df = DataFrame(data)  # really we are only plotting DataFrames
    df, kwargs_d = constrain_data(df, **kwargs)
    item_count = len(df.columns)

    # --- deal with complete PeriodIdex indicies
    if not is_categorical(df):
        print("Warning: bar_plot is not designed for incomplete or non-categorical data indexes.")
    saved_pi = map_periodindex(df)
    if saved_pi is not None:
        df = saved_pi[0]  # extract the reindexed DataFrame from the PeriodIndex

    # --- set up the default arguments
    chart_defaults: dict[str, Any] = {
        "stacked": False,
        "max_ticks": 10,
        "label_series": item_count > 1,
    }
    chart_args = {k: kwargs_d.get(k, v) for k, v in chart_defaults.items()}

    bar_defaults: dict[str, Any] = {
        "color": get_color_list(item_count),
        "width": get_setting("bar_width"),
        "label_series": (item_count > 1),
    }
    above = kwargs_d.get("above", False)
    anno_args: dict[str, Any] = {
        "annotate": kwargs_d.get("annotate", False),
        "fontsize": kwargs_d.get("fontsize", "small"),
        "fontname": kwargs_d.get("fontname", "Helvetica"),
        "rotation": kwargs_d.get("rotation", 0),
        "rounding": kwargs_d.get("rounding", True),
        "color": kwargs_d.get("annotate_color", "black" if above else "white"),
        "above": above,
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, bar_defaults, kwargs_d)

    # --- plot the data
    axes, remaining_kwargs = get_axes(**remaining_kwargs)
    if chart_args["stacked"]:
        stacked(axes, df, anno_args, **bar_args)
    else:
        grouped(axes, df, anno_args, **bar_args)

    # --- handle complete periodIndex data and label rotation
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], chart_args["max_ticks"])
    else:
        plt.xticks(rotation=90)

    return axes
