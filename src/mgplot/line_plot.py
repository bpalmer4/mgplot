"""
line_plot.py:
Plot a series or a dataframe over multiple (starting_point) time horizons.
"""

# --- imports
import math
from typing import Any, cast

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame, Series

from mgplot.finalise_plot import finalise_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import apply_defaults, get_color_list
from mgplot.settings import set_chart_dir, clear_chart_dir


# --- constants
STARTS, TAGS = "starts", "tags"
AX = "ax"
STYLE, WIDTH, COLOR = "style", "width", "color"
ANNOTATE = "annotate"
ALPHA, LEGEND, DROPNA = "alpha", "legend", "dropna"
DRAWSTYLE, MARKER = "drawstyle", "marker"
MARKERSIZE = "markersize"


# --- functions
# private
def _get_multi_starts(**kwargs) -> tuple[dict[str, list], dict]:
    """Get the multi-starting point arguments."""

    defaults = {  # defaults
        STARTS: None,  # should be first item in dictionary
        TAGS: "",
    }
    stags, kwargs = apply_defaults(1, defaults, kwargs)

    if len(stags[TAGS]) < len(stags[STARTS]):
        stags[TAGS] = stags[TAGS] * len(stags[STARTS])
    # Ensure that the tags are not identical ...
    if len(stags[TAGS]) > 1 and stags[TAGS].count(stags[TAGS][0]) == len(stags[TAGS]):
        stags[TAGS] = [
            e + f"{i:05d}" if i > 0 else e for i, e in enumerate(stags[TAGS])
        ]

    return stags, kwargs


def _get_style_width_color_etc(
    item_count, num_data_points, **kwargs
) -> tuple[dict[str, list], dict]:
    """Get the plot-line attributes arguemnts.
    Returns a dictionary of lists of attributes for each line, and
    a modified kwargs dictionary."""

    color = kwargs.get(COLOR, get_color_list(item_count))

    data_point_thresh = 24
    defaults: dict[str, Any] = {
        STYLE: "-",
        WIDTH: (
            get_setting("line_normal") if num_data_points > data_point_thresh
            else get_setting("line_wide")
        ),
        COLOR: color,
        ALPHA: 1.0,
        DRAWSTYLE: None,
        MARKER: None,
        MARKERSIZE: 10,
        ANNOTATE: False,
    }
    swce, kwargs = apply_defaults(item_count, defaults, kwargs)

    swce[LEGEND] = kwargs.get(LEGEND, None)
    if swce[LEGEND] is None and item_count > 1:
        swce[LEGEND] = get_setting("legend_style")
    if LEGEND in kwargs:
        del kwargs[LEGEND]

    swce[DROPNA] = kwargs.get(DROPNA, False)
    if DROPNA in kwargs:
        del kwargs[DROPNA]

    return swce, kwargs


def _annotate(
    axes: plt.Axes,
    series: Series,
    color: str = "#444444",
    fontsize: int = 10,
) -> None:
    """Annotate the right-hand end-point of a line-plotted series."""

    x, y = series.index[-1], series.iloc[-1]
    if y is None or math.isnan(y):
        return

    rounding: int = 0 if y >= 100 else 1 if y >= 10 else 2
    axes.text(
        x=x,
        y=y,
        s=f" {y:.{rounding}f}",
        ha="left",
        va="center",
        fontsize=fontsize,
        color=color,
        font="Helvetica",
    )


# public
def line_plot(data: DataT, **kwargs: Any) -> None:
    """Plot a series or a dataframe over multiple (starting_point) time horizons.
    The data must be a pandas Series or DataFrame with a PeriodIndex.
    Arguments:
    - starts - str| pd.Period | list[str] | list[pd.Period] -
      starting dates for plots.
    - tags - str | list[str] - unique file name tages for multiple plots.
    - color - str | list[str] - line colors.
    - width - float | list[float] - line widths.
    - style - str | list[str] - line styles.
    - alpha - float | list[float] - line transparencies.
    - annotate - bool | list bool - whether to annotate the end-point of the line.
    - legend - dict | False - arguments to splat in a call to plt.Axes.legend()
    - drawstyle - str | list[str] - pandas drawing style
      if False, no legend will be displayed.
    - dropna - bool - whether to delete NAs before plotting
    - ax - plt.Axes | None - axes to plot on (optional)
    - Remaining arguments as for finalise_plot() [but note, the tag
      argument to finalise_plot cannot be used. Use tags instead.]"""

    # sanity checks
    if not isinstance(data, (Series, DataFrame)) or not isinstance(
        data.index, pd.PeriodIndex
    ):
        raise TypeError(
            "The data argument must be a pandas Series or DataFrame with a PeriodIndex"
        )
    if AX in kwargs and kwargs[AX] is not None and STARTS in kwargs:
        print("Caution: only one chart can be plotted with the passed axes")

    # really we are only plotting DataFrames
    df = DataFrame(data)

    # get extra plotting parameters - not passed to finalise_plot()
    item_count = len(df.columns)
    num_data_points = len(df)
    stags, kwargs = _get_multi_starts(**kwargs)  # time horizons
    swce, kwargs = _get_style_width_color_etc(
        item_count, num_data_points, **kwargs
    )  # lines

    # And plot
    for start, tag in zip(stags[STARTS], stags[TAGS]):
        if start and not isinstance(start, pd.Period):
            start = pd.Period(start, freq=cast(pd.PeriodIndex, df.index).freq)
        recent = df[df.index >= start] if start else df
        # note cammot use ax and start/tag in finalise_plot
        axes: None | plt.Axes = kwargs.pop(AX, None)
        for i, column in enumerate(recent):
            if (recent[column].isna()).all():
                continue
            series = (
                recent[column].dropna()
                if DROPNA in swce and swce[DROPNA]
                else recent[column]
            )
            axes = series.plot(
                ls=swce[STYLE][i],
                lw=swce[WIDTH][i],
                color=swce[COLOR][i],
                alpha=swce[ALPHA][i],
                marker=swce[MARKER][i],
                ms=swce[MARKERSIZE][i],
                drawstyle=swce[DRAWSTYLE][i],
                ax=axes,
            )
            if swce[ANNOTATE][i] and axes is not None:
                _annotate(axes, series, swce[COLOR][i])

        if LEGEND in swce and isinstance(swce[LEGEND], dict):
            kwargs[LEGEND] = swce[LEGEND].copy()
        if axes:
            finalise_plot(axes, tag=tag, **kwargs)


def seas_trend_plot(data: DataFrame, **kwargs) -> None:
    """Plot a DataFrame, where the first column is seasonally
    adjusted data, and the second column is trend data."""

    colors = get_color_list(2)
    widths = [get_setting("line_normal"), get_setting("line_wide")]
    annotations = [True, False]
    styles = "-"

    if DROPNA not in kwargs:
        kwargs[DROPNA] = True

    line_plot(
        data,
        width=widths,
        color=colors,
        style=styles,
        annotate=kwargs.get(ANNOTATE, annotations),
        legend=kwargs.get(LEGEND, get_setting("legend_style")),
        **kwargs,
    )


if __name__ == "__main__":
    # test code

    # set/clear the chart directory
    set_chart_dir("./test_charts")
    clear_chart_dir()

    # Create a sample DataFrame with a PeriodIndex
    np.random.seed(42)
    dates = pd.period_range("2020-01", "2020-12", freq="M")
    data_ = pd.DataFrame(
        {
            "Series1": np.random.rand(len(dates)),
            "Series2": np.random.rand(len(dates)),
        },
        index=dates,
    )

    # Call the line_plot function with the sample data
    line_plot(data_, title="Test Plot", xlabel="Date", ylabel="Value", annotate=True)
