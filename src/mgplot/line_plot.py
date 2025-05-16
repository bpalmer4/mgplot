"""
line_plot.py:
Plot a series or a dataframe with lines.
"""

# --- imports
from typing import Any, cast

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame

from mgplot.finalise_plot import finalise_plot, get_finalise_kwargs_list
from mgplot.settings import DataT, get_setting
from mgplot.utilities import apply_defaults, get_color_list, get_axes, annotate_series
from mgplot.settings import set_chart_dir


# --- constants
STARTS, TAGS = "starts", "tags"
AX = "ax"
STYLE, WIDTH, COLOR = "style", "width", "color"
ANNOTATE = "annotate"
ALPHA, LEGEND, DROPNA = "alpha", "legend", "dropna"
DRAWSTYLE, MARKER = "drawstyle", "marker"
MARKERSIZE = "markersize"


# --- functions
def _get_style_width_color_etc(
    item_count, num_data_points, **kwargs
) -> tuple[dict[str, list], dict]:
    """
    Get the plot-line attributes arguemnts.
    Returns a dictionary of lists of attributes for each line, and
    a modified kwargs dictionary.
    """

    data_point_thresh = 24
    defaults: dict[str, Any] = {
        STYLE: "-",
        WIDTH: (
            get_setting("line_normal")
            if num_data_points > data_point_thresh
            else get_setting("line_wide")
        ),
        COLOR: kwargs.get(COLOR, get_color_list(item_count)),
        ALPHA: 1.0,
        DRAWSTYLE: None,
        MARKER: None,
        MARKERSIZE: 10,
        ANNOTATE: None,
    }
    swce, kwargs = apply_defaults(item_count, defaults, kwargs)

    swce[DROPNA] = kwargs.get(DROPNA, False)
    if DROPNA in kwargs:
        del kwargs[DROPNA]

    return swce, kwargs


def line_plot(data: DataT, **kwargs) -> plt.Axes:
    """
    Build a single plot from the data passed in.
    This can be a single or multiple line plot.
    Return the axes object for the build.

    Agruments:
    - data: DataFrame | Series - data to plot
    - kwargs:
        - color: str | list[str] - line colors.
        - width: float | list[float] - line widths [optional].
        - style: str | list[str] - line styles [optional].
        - alpha: float | list[float] - line transparencies [optional].
        - marker: str | list[str] - line markers [optional].
        - marker_size: float | list[float] - line marker sizes [optional].
        - annotate: None | int | list[int] -  if not None, the number
          of decimals with which to annotate the right-end-point of a line.
        - dropna: bool | list[bool] - whether to delete NAs before plotting
          [optional]
        - ax: plt.Axes | None - axes to plot on (optional)
        - figsize: tuple[float, float] - figure size (optional)

    Returns:
    - axes: plt.Axes - the axes object for the plot
    """

    # the data to be plotted:
    df = DataFrame(data)  # really we are only plotting DataFrames
    item_count = len(df.columns)
    num_data_points = len(df)
    swce, kwargs = _get_style_width_color_etc(item_count, num_data_points, **kwargs)

    # Let's plot
    axes, kwargs = get_axes(kwargs)  # get the axes to plot on
    for i, column in enumerate(df.columns):
        series = df[column]
        if (series.isna()).all():
            continue
        series = series.dropna() if DROPNA in swce and swce[DROPNA] else series
        if series.empty or series.isna().all():
            continue
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
        if swce[ANNOTATE][i]:
            rounding: int | None = (
                swce[ANNOTATE][i] if isinstance(swce[ANNOTATE][i], int) else None
            )
            annotate_series(series, axes, rounding=rounding, color=swce[COLOR][i])

    return axes


def line_plot_finalise(data: DataT, **kwargs) -> None:
    """
    Publish a single plot from the data passed in.

    Arguments:
        Use the same arguments as for line_plot() and finalise_plot().

    Returns:
        None.
    """

    axes = line_plot(data, **kwargs)
    keep_me = get_finalise_kwargs_list()
    fp_kwargs = {k: v for k, v in kwargs.items() if k in keep_me}
    finalise_plot(axes, **fp_kwargs)


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


def line_plot_multistart(data: DataT, **kwargs) -> None:
    """
    Publish multiple plots from the data passed in, with multiple starting
    points, Each plot is finalised with a call to finalise_plot().
    Note: the data must be a pandas Series or DataFrame with a PeriodIndex.

    Arguments:
    In addition to using much the same arguments for line_plot() and
    finalise_plot(), the following arguments are also used:
    - starts: str | pd.Period | list[str] | list[pd.Period] -
      starting dates for plots.
    - tags: str | list[str] - unique file name tages for multiple plots.
    Note: cannot use the ax argument to line_plot()

    Returns
    - None.
    """

    stags, rkwargs = _get_multi_starts(**kwargs)  # time horizons
    if AX in rkwargs:
        print("Ignoring the ax argument to line_plot_multistart()")
        del rkwargs[AX]

    previous_tags: set[str] = set()
    counter = 0
    for start, tag in zip(stags[STARTS], stags[TAGS]):
        if start and not isinstance(start, pd.Period):
            start = pd.Period(start, freq=cast(pd.PeriodIndex, start.index).freq)
        recent = data[data.index >= start] if start else data
        this_kwargs = rkwargs.copy()
        proposed_tag = tag
        while proposed_tag in previous_tags:
            counter += 1
            proposed_tag = f"{tag}_{counter:05d}"
        this_kwargs["tag"] = proposed_tag
        line_plot_finalise(recent, **this_kwargs)


def seas_trend_plot(data: DataFrame, **kwargs) -> None:
    """
    Publish a DataFrame, where the first column is seasonally
    adjusted data, and the second column is trend data.

    Aguments:
    - data: DataFrame - the data to plot with the first column
      being the seasonally adjusted data, and the second column
      being the trend data.
    The remaining arguments are the same as those passed to
    (1) line_plot() and then (2) finalise_plot().

    Returns:
    - None
    """

    colors = get_color_list(2)
    widths = [get_setting("line_normal"), get_setting("line_wide")]
    annotations = [True, False]
    styles = "-"

    if DROPNA not in kwargs:
        kwargs[DROPNA] = True

    annotate = (kwargs.pop(ANNOTATE, annotations),)
    legend = (kwargs.pop(LEGEND, get_setting("legend")),)
    line_plot_finalise(
        data,
        width=widths,
        color=colors,
        style=styles,
        annotate=annotate,
        legend=legend,
        **kwargs,
    )


# --- test code
if __name__ == "__main__":

    # set the chart directory
    set_chart_dir("./test_charts")

    # Create a sample DataFrame with a PeriodIndex
    np.random.seed(42)
    dates = pd.period_range("2020-01", "2025-01", freq="M")
    data_ = pd.DataFrame(
        {
            "Series 1": np.random.rand(len(dates)),
            "Series 2": np.random.rand(len(dates)),
        },
        index=dates,
    )

    # Call the line_plot function with the sample data
    line_plot_finalise(
        data_,
        title="Test Line Plot",
        xlabel=None,
        ylabel="Value",
        width=[3, 1.5],
        marker=[None, "o"],
        markersize=[None, 5],
        legend=True,
        annotate=3,
    )
