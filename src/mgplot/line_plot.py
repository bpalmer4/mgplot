"""
line_plot.py:
Plot a series or a dataframe with lines.
"""

# --- imports
from typing import Any
from collections.abc import Sequence
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame

from mgplot.settings import DataT, get_setting
from mgplot.kw_type_checking import (
    report_kwargs,
    validate_kwargs,
    validate_expected,
    ExpectedTypeDict,
    limit_kwargs,
)
from mgplot.finalise_plot import finalise_plot, FINALISE_KW_TYPES
from mgplot.utilities import (
    apply_defaults,
    get_color_list,
    get_axes,
    annotate_series,
)
from mgplot.test import prepare_for_test


# --- constants
DATA = "data"
AX = "ax"
STYLE, WIDTH, COLOR, ALPHA = "style", "width", "color", "alpha"
ANNOTATE = "annotate"
ROUNDING = "rounding"
FONTSIZE = "fontsize"
DROPNA = "dropna"
DRAWSTYLE, MARKER, MARKERSIZE = "drawstyle", "marker", "markersize"

LP_KW_TYPES: ExpectedTypeDict = {
    AX: (plt.Axes, type(None)),
    STYLE: (str, Sequence, (str,)),
    WIDTH: (float, int, Sequence, (float, int)),
    COLOR: (str, Sequence, (str,)),
    ALPHA: (float, Sequence, (float,)),
    DRAWSTYLE: (str, Sequence, (str,), type(None)),
    MARKER: (str, Sequence, (str,), type(None)),
    MARKERSIZE: (float, Sequence, (float,), int, type(None)),
    DROPNA: (bool, Sequence, (bool,)),
    ANNOTATE: (bool, Sequence, (bool,)),
    ROUNDING: (Sequence, (bool, int), int, bool, type(None)),
    FONTSIZE: (Sequence, (str, int), str, int, type(None)),
}
validate_expected(LP_KW_TYPES, "line_plot")

LEGEND = "legend"


# --- functions
def _get_style_width_color_etc(
    item_count, num_data_points, **kwargs
) -> tuple[dict[str, list | tuple], dict[str, Any]]:
    """
    Get the plot-line attributes arguemnts.
    Returns a dictionary of lists of attributes for each line, and
    a modified kwargs dictionary.
    """

    data_point_thresh = 151
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
        DROPNA: True,
        ANNOTATE: False,
        ROUNDING: True,
        FONTSIZE: "small",
    }

    return apply_defaults(item_count, defaults, kwargs)


def line_plot(data: DataT, **kwargs) -> plt.Axes:
    """
    Build a single plot from the data passed in.
    This can be a single- or multiple-line plot.
    Return the axes object for the build.

    Agruments:
    - data: DataFrame | Series - data to plot
    - kwargs:
        - ax: plt.Axes | None - axes to plot on (optional)
        - dropna: bool | list[bool] - whether to delete NAs frm the
          data before plotting [optional]
        - color: str | list[str] - line colors.
        - width: float | list[float] - line widths [optional].
        - style: str | list[str] - line styles [optional].
        - alpha: float | list[float] - line transparencies [optional].
        - marker: str | list[str] - line markers [optional].
        - marker_size: float | list[float] - line marker sizes [optional].
        - annotate: bool | list[bool] - whether to annotate a series.
        - rounding: int | bool | list[int | bool] - number of decimal places
          to round an annotation. If True, a default between 0 and 2 is
          used.
        - fontsize: int | str | list[int | str] - font size for the
          annotation.
        - drawstyle: str | list[str] - matplotlib line draw styles.

    Returns:
    - axes: plt.Axes - the axes object for the plot
    """

    # sanity checks
    report_kwargs(kwargs, called_from="line_plot")
    validate_kwargs(kwargs, LP_KW_TYPES, called_from="line_plot")

    # the data to be plotted:
    df = DataFrame(data)  # really we are only plotting DataFrames

    # get the arguments for each line we will plot ...
    item_count = len(df.columns)
    num_data_points = len(df)
    swce, kwargs = _get_style_width_color_etc(item_count, num_data_points, **kwargs)

    # Let's plot
    axes, kwargs = get_axes(kwargs)  # get the axes to plot on
    for i, column in enumerate(df.columns):
        series = df[column]
        series = series.dropna() if DROPNA in swce and swce[DROPNA][i] else series
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

        if swce[ANNOTATE][i] is None or not swce[ANNOTATE][i]:
            continue

        annotate_series(
            series,
            axes,
            rounding=swce[ROUNDING][i],
            color=swce[COLOR][i],
            fontsize=swce[FONTSIZE][i],
        )

    return axes


def line_plot_finalise(data: DataT, **kwargs) -> None:
    """
    Publish a single plot from the data passed in.

    Arguments:
    - data: DataFrame | Series - data to plot
    - Use the same  keyword arguments as for line_plot()
      and finalise_plot().

    Returns None.
    """

    # sanity checks
    kw_dict = LP_KW_TYPES | FINALISE_KW_TYPES
    validate_kwargs(kwargs, kw_dict, "line_plot_finalise")
    report_kwargs(kwargs, called_from="line_plot_finalise")

    # if multi-column, assume we want a legend
    if isinstance(data, pd.DataFrame) and len(data.columns) > 1:
        kwargs[LEGEND] = kwargs.get(LEGEND, get_setting("legend"))

    # plot the data
    lp_kwargs = limit_kwargs(kwargs, LP_KW_TYPES)
    axes = line_plot(data, **lp_kwargs)

    # finalise the plot
    fp_kwargs = limit_kwargs(kwargs, FINALISE_KW_TYPES)
    finalise_plot(axes, **fp_kwargs)


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

    # defaults if not in kwargs
    colors = kwargs.pop(COLOR, get_color_list(2))
    widths = kwargs.pop(WIDTH, [get_setting("line_normal"), get_setting("line_wide")])
    styles = kwargs.pop(STYLE, ["-", "-"])
    annotations = kwargs.pop(ANNOTATE, [True, False])
    rounding = kwargs.pop(ROUNDING, True)
    legend = kwargs.pop(LEGEND, True)

    # series breaks are common in seas-trend data
    kwargs[DROPNA] = kwargs.pop(DROPNA, False)

    line_plot_finalise(
        data,
        color=colors,
        width=widths,
        style=styles,
        annotate=annotations,
        rounding=rounding,
        legend=legend,
        **kwargs,
    )


# --- test code
if __name__ == "__main__":

    # set the chart directory
    prepare_for_test("line_plot")

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
        annotate=[True, False],
        rounding=True,
    )
