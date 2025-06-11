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
from mgplot.keyword_names import (
    AX,
    DROPNA,
    PLOT_FROM,
    LABEL_SERIES,
    STYLE,
    DRAWSTYLE,
    MARKER,
    MARKERSIZE,
    WIDTH,
    COLOR,
    ALPHA,
    ANNOTATE,
    ROUNDING,
    FONTSIZE,
    FONTNAME,
    ROTATION,
    ANNOTATE_COLOR,
)

# --- constants
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
    FONTSIZE: (Sequence, (str, int, float), str, int, float),
    FONTNAME: (str, Sequence, (str,)),
    ROTATION: (int, float, Sequence, (int, float)),
    ANNOTATE_COLOR: (str, Sequence, (str,), bool, Sequence, (bool,), type(None)),
    PLOT_FROM: (int, Period, type(None)),
    LABEL_SERIES: (bool, Sequence, (bool,), type(None)),
}
validate_expected(LINE_KW_TYPES, "line_plot")


# --- functions
def annotate_series(
    series: Series,
    axes: Axes,
    **kwargs,  # "fontsize", "rounding",
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
    fontsize = kwargs.get(FONTSIZE, "small")
    if fontsize is None or isinstance(fontsize, bool):
        fontsize = "small"
    fontname = kwargs.get(FONTNAME, "Helvetica")
    rotation = kwargs.get(ROTATION, 0)

    # --- add the annotation
    color = kwargs["color"]
    rounding = default_rounding(value=y, provided=kwargs.get(ROUNDING, None))
    r_string = f"  {y:.{rounding}f}" if rounding > 0 else f"  {int(y)}"
    axes.text(
        x=x,
        y=y,
        s=r_string,
        ha="left",
        va="center",
        fontsize=fontsize,
        font=fontname,
        rotation=rotation,
        color=color,
    )


def _get_style_width_color_etc(
    item_count, num_data_points, **kwargs
) -> tuple[dict[str, list | tuple], dict[str, Any]]:
    """
    Get the plot-line attributes arguemnts.
    Returns a dictionary of lists of attributes for each line, and
    a modified kwargs dictionary.
    """

    data_point_thresh = 151  # switch from wide to narrow lines
    line_defaults: dict[str, Any] = {
        STYLE: "solid" if item_count < 4 else ["solid", "dashed", "dashdot", "dotted"],
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
        FONTNAME: "Helvetica",
        ROTATION: 0,
        ANNOTATE_COLOR: True,
        LABEL_SERIES: True,
    }

    return apply_defaults(item_count, line_defaults, kwargs)


def line_plot(data: DataT, **kwargs) -> Axes:
    """
    Build a single plot from the data passed in.
    This can be a single- or multiple-line plot.
    Return the axes object for the build.

    Agruments:
    - data: DataFrame | Series - data to plot
    - kwargs:
        /* chart wide arguments */
        - ax: Axes | None - axes to plot on (optional)
        /* individual line arguments */
        - dropna: bool | list[bool] - whether to delete NAs frm the
          data before plotting [optional]
        - color: str | list[str] - line colors.
        - width: float | list[float] - line widths [optional].
        - style: str | list[str] - line styles [optional].
        - alpha: float | list[float] - line transparencies [optional].
        - marker: str | list[str] - line markers [optional].
        - marker_size: float | list[float] - line marker sizes [optional].
        /* end of line annotation arguments */
        - annotate: bool | list[bool] - whether to annotate a series.
        - rounding: int | bool | list[int | bool] - number of decimal places
          to round an annotation. If True, a default between 0 and 2 is
          used.
        - fontsize: int | str | list[int | str] - font size for the
          annotation.
        - fontname: str - font name for the annotation.
        - rotation: int | float | list[int | float] - rotation of the
          annotation text.
        - drawstyle: str | list[str] - matplotlib line draw styles.
        - annotate_color: str | list[str] | bool | list[bool] - color
          for the annotation text.  If True, the same color as the line.

    Returns:
    - axes: Axes - the axes object for the plot
    """

    # --- check the kwargs
    me = "line_plot"
    report_kwargs(called_from=me, **kwargs)
    kwargs = validate_kwargs(LINE_KW_TYPES, me, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, me)
    df = DataFrame(data)  # we are only plotting DataFrames
    df, kwargs = constrain_data(df, **kwargs)

    # --- some special defaults
    kwargs[LABEL_SERIES] = (
        kwargs.get(LABEL_SERIES, True)
        if len(df.columns) > 1
        else kwargs.get(LABEL_SERIES, False)
    )

    # --- Let's plot
    axes, kwargs = get_axes(**kwargs)  # get the axes to plot on
    if df.empty or df.isna().all().all():
        # Note: finalise plot should ignore an empty axes object
        print(f"Warning: No data to plot in {me}().")
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

        series.plot(
            # Note: pandas will plot PeriodIndex against their ordinal values
            ls=swce[STYLE][i],
            lw=swce[WIDTH][i],
            color=swce[COLOR][i],
            alpha=swce[ALPHA][i],
            marker=swce[MARKER][i],
            ms=swce[MARKERSIZE][i],
            drawstyle=swce[DRAWSTYLE][i],
            label=(
                column
                if LABEL_SERIES in swce and swce[LABEL_SERIES][i]
                else f"_{column}_"
            ),
            ax=axes,
        )

        if swce[ANNOTATE][i] is None or not swce[ANNOTATE][i]:
            continue

        color = (
            swce[COLOR][i]
            if swce[ANNOTATE_COLOR][i] is True
            else swce[ANNOTATE_COLOR][i]
        )
        annotate_series(
            series,
            axes,
            color=color,
            rounding=swce[ROUNDING][i],
            fontsize=swce[FONTSIZE][i],
            fontname=swce[FONTNAME][i],
            rotation=swce[ROTATION][i],
        )

    return axes
