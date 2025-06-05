"""
line_plot.py:
Plot a series or a dataframe with lines.
"""

# --- imports
from typing import Any
import math
from collections.abc import Sequence
from matplotlib.pyplot import Axes
from pandas import DataFrame, Series, Period

from mgplot.settings import DataT, get_setting
from mgplot.finalise_plot import make_legend
from mgplot.kw_type_checking import (
    report_kwargs,
    validate_kwargs,
    validate_expected,
    ExpectedTypeDict,
)
from mgplot.utilities import (
    apply_defaults,
    get_color_list,
    get_axes,
    constrain_data,
    check_clean_timeseries,
    default_rounding,
)


# --- constants
DATA = "data"
AX = "ax"
STYLE, WIDTH, COLOR, ALPHA = "style", "width", "color", "alpha"
ANNOTATE = "annotate"
ROUNDING = "rounding"
FONTSIZE = "fontsize"
ANNOTATE_COLOR = "annotate_color"  # color for the annotation text
DROPNA = "dropna"
DRAWSTYLE, MARKER, MARKERSIZE = "drawstyle", "marker", "markersize"
PLOT_FROM = "plot_from"  # used to constrain the data to a starting point
LEGEND = "legend"

LINE_KW_TYPES: ExpectedTypeDict = {
    AX: (Axes, type(None)),
    STYLE: (str, Sequence, (str,)),
    WIDTH: (float, int, Sequence, (float, int)),
    COLOR: (str, Sequence, (str,)),  # line color
    ALPHA: (float, Sequence, (float,)),
    DRAWSTYLE: (str, Sequence, (str,), type(None)),
    MARKER: (str, Sequence, (str,), type(None)),
    MARKERSIZE: (float, Sequence, (float,), int, type(None)),
    DROPNA: (bool, Sequence, (bool,)),
    ANNOTATE: (bool, Sequence, (bool,)),
    ROUNDING: (Sequence, (bool, int), int, bool, type(None)),
    FONTSIZE: (Sequence, (str, int), str, int, type(None)),
    ANNOTATE_COLOR: (str, Sequence, (str,), type(None)),
    PLOT_FROM: (int, Period, type(None)),
    LEGEND: (dict, (str, object), bool, type(None)),
}
validate_expected(LINE_KW_TYPES, "line_plot")


# --- functions
def annotate_series(
    series: Series,
    axes: Axes,
    **kwargs,  # "fontsize", "rounding", "annotate_color"
) -> None:
    """Annotate the right-hand end-point of a line-plotted series."""

    # --- check the series has a value to annotate
    latest = series.dropna()
    if series.empty:
        return
    x, y = latest.index[-1], latest.iloc[-1]
    if y is None or math.isnan(y):
        return

    # --- extract fontsize - could be None, bool, int or str.
    fontsize = kwargs.get("fontsize", "small")
    if fontsize is None or isinstance(fontsize, bool):
        fontsize = "small"

    # --- extract rounding - could be None, bool or int
    rounding = default_rounding(y)  # the case for None or bool
    if "rounding" in kwargs:
        possible = kwargs["rounding"]
        if not isinstance(possible, bool):
            if isinstance(possible, int):
                rounding = possible

    # --- do the rounding
    r_string = f"  {int(y)}"  # default to no rounding
    if rounding > 0:
        r_string = f"  {y:.{rounding}f}"

    # --- add the annotation
    if "test" in kwargs and kwargs["test"]:
        print(f"annotate_series: {x=}, {y=}, {rounding=} {r_string=}")
        return

    color = kwargs.get("annotate_color", "black")
    axes.text(
        x=x,
        y=y,
        s=r_string,
        ha="left",
        va="center",
        fontsize=fontsize,
        color=color,
        font="Helvetica",
    )


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
        COLOR: get_color_list(item_count),
        ALPHA: 1.0,
        DRAWSTYLE: None,
        MARKER: None,
        MARKERSIZE: 10,
        DROPNA: True,
        ANNOTATE: False,
        ROUNDING: True,
        FONTSIZE: "small",
        ANNOTATE_COLOR: "black",
    }

    return apply_defaults(item_count, defaults, kwargs)


def line_plot(data: DataT, **kwargs) -> Axes:
    """
    Build a single plot from the data passed in.
    This can be a single- or multiple-line plot.
    Return the axes object for the build.

    Agruments:
    - data: DataFrame | Series - data to plot
    - kwargs:
        - ax: Axes | None - axes to plot on (optional)
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
    - axes: Axes - the axes object for the plot
    """

    # --- check the kwargs
    me = "line_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(LINE_KW_TYPES, me, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, me)
    df = DataFrame(data)  # really we are only plotting DataFrames
    df, kwargs = constrain_data(df, **kwargs)

    # --- some special defaults
    if len(df.columns) > 1:
        # default to displaying a legend
        kwargs["legend"] = kwargs.get("legend", True)
    if len(df.columns) > 4:
        # default to using a style for the lines
        kwargs["style"] = kwargs.get("style", ["solid", "dashed", "dashdot", "dotted"])

    # --- Let's plot
    axes, kwargs = get_axes(**kwargs)  # get the axes to plot on
    if df.empty or df.isna().all().all():
        # Note: finalise plot will ignore an empty axes object
        print("Warning: No data to plot.")
        return axes

    # --- get the arguments for each line we will plot ...
    item_count = len(df.columns)
    num_data_points = len(df)
    swce, kwargs = _get_style_width_color_etc(item_count, num_data_points, **kwargs)

    for i, column in enumerate(df.columns):
        series = df[column]
        series = series.dropna() if DROPNA in swce and swce[DROPNA][i] else series
        if series.empty or series.isna().all():
            print(f"Warning: No data to plot for {column} in line_plot().")
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
            color=swce[ANNOTATE_COLOR][i],
            fontsize=swce[FONTSIZE][i],
        )

    # add a legend if requested
    if len(df.columns) > 1:
        kwargs[LEGEND] = kwargs.get(LEGEND, get_setting("legend"))

    if LEGEND in kwargs:
        make_legend(axes, kwargs[LEGEND])

    return axes
