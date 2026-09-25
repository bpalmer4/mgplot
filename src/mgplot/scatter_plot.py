"""Plot one numeric column against another as a scatter plot.

Unlike the other mgplot plot functions, the index is not plotted. It is only
used to find the latest observation (for highlight_latest) and, when it is a
PeriodIndex or an integer index, to apply plot_from.
"""

from typing import Any, Final, NotRequired, Unpack

import numpy as np
from matplotlib.axes import Axes
from pandas import DataFrame, Period, PeriodIndex, Series
from pandas.api.types import is_integer_dtype, is_numeric_dtype

from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting
from mgplot.utilities import constrain_data, get_axes, get_color_list

# --- constants
ME: Final[str] = "scatter_plot"
REQUIRED_COLUMNS: Final[int] = 2  # x first, y second
DEFAULT_SIZE: Final[float] = 12  # marker area (matplotlib s=)
DEFAULT_ALPHA: Final[float] = 0.6
DEFAULT_MARKER: Final[str] = "o"
DEFAULT_POINTS_ZORDER: Final[float] = 1  # matplotlib's default for collections
LATEST_SIZE_MULTIPLE: Final[float] = 16  # highlighted point area relative to the others
DIAGONAL_LABEL: Final[str] = "45° (equal)"
DIAGONAL_COLOR: Final[str] = "darkred"
CORR_DECIMALS: Final[int] = 2


class ScatterKwargs(BaseKwargs):
    """Keyword arguments for the scatter_plot function."""

    ax: NotRequired[Axes | None]
    color: NotRequired[str]
    size: NotRequired[float | int]
    alpha: NotRequired[float]
    marker: NotRequired[str]
    label: NotRequired[str | None]
    zorder: NotRequired[int | float]
    dropna: NotRequired[bool]
    plot_from: NotRequired[int | Period | None]
    diagonal: NotRequired[bool | dict[str, Any]]
    fit: NotRequired[bool | dict[str, Any]]
    highlight_latest: NotRequired[bool | dict[str, Any]]
    report_corr: NotRequired[bool]


# --- private functions
def _check_data(data: object) -> DataFrame:
    """Confirm data is a DataFrame with exactly two numeric columns (x, y)."""
    if not isinstance(data, DataFrame):
        raise TypeError(
            f"{ME}() expects a DataFrame with two numeric columns (x, y), not a {type(data).__name__}."
        )
    if len(data.columns) != REQUIRED_COLUMNS:
        raise ValueError(
            f"{ME}() expects exactly two columns (x first, y second), but got {len(data.columns)}."
        )
    non_numeric = [str(c) for c in data.columns if not is_numeric_dtype(data[c])]
    if non_numeric:
        raise ValueError(f"{ME}() expects numeric columns, but these are not: {', '.join(non_numeric)}.")
    return data


def _constrain(df: DataFrame, kwargs_d: dict[str, Any]) -> tuple[DataFrame, dict[str, Any]]:
    """Apply plot_from, when provided, to the data."""
    if kwargs_d.get("plot_from") is None:
        kwargs_d.pop("plot_from", None)
        return df, kwargs_d
    if not isinstance(df.index, PeriodIndex) and not is_integer_dtype(df.index):
        print(f"Warning: plot_from ignored in {ME}(); the index is neither a PeriodIndex nor integer.")
        kwargs_d.pop("plot_from", None)
        return df, kwargs_d
    return constrain_data(df, **kwargs_d)


def _style(spec: object, house: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve an overlay spec: True -> house style, dict -> merged over house style, else None."""
    if spec is True:
        return dict(house)
    if isinstance(spec, dict):
        return house | spec
    return None


def _points_label(label: object, x: Series, y: Series, *, report_corr: bool) -> str | None:
    """Return the legend label for the points, with the correlation appended if requested."""
    text = label if isinstance(label, str) else None
    if not report_corr:
        return text
    r = x.corr(y)
    if not isinstance(r, float) or np.isnan(r):
        print(f"Warning: correlation is undefined in {ME}(), so it has not been reported.")
        return text
    corr = f"r = {r:.{CORR_DECIMALS}f}"
    return corr if text is None else f"{text} ({corr})"


def _draw_diagonal(axes: Axes, spec: object) -> None:
    """Draw the y = x line across the range covering the data on both axes."""
    style = _style(
        spec,
        {"color": DIAGONAL_COLOR, "ls": "--", "lw": get_setting("line_narrow"), "label": DIAGONAL_LABEL},
    )
    if style is None:
        return
    limits = axes.dataLim  # covers everything already plotted on these axes
    low = min(limits.x0, limits.y0)
    high = max(limits.x1, limits.y1)
    axes.plot([low, high], [low, high], **style)


def _draw_fit(axes: Axes, x: Series, y: Series, spec: object, color: str) -> None:
    """Draw the OLS line of best fit across the x-range of the points."""
    style = _style(spec, {"color": color, "lw": get_setting("line_normal")})
    if style is None:
        return
    if x.nunique() < REQUIRED_COLUMNS:
        print(f"Warning: a line of best fit needs at least two distinct x values in {ME}().")
        return
    slope, intercept = np.polyfit(x.to_numpy(dtype=float), y.to_numpy(dtype=float), 1)
    ends = np.array([x.min(), x.max()], dtype=float)
    axes.plot(ends, slope * ends + intercept, **style)


def _draw_latest(axes: Axes, df: DataFrame, spec: object, points: dict[str, Any]) -> None:
    """Redraw the point with the latest index value, larger and as a star."""
    position = int(df.index.argmax())
    latest = df.index[position]
    style = _style(
        spec,
        {
            "color": points["color"],
            "s": points["s"] * LATEST_SIZE_MULTIPLE,
            "marker": "*",
            "edgecolors": "black",
            "linewidths": get_setting("line_narrow"),
            "zorder": points["zorder"] + 1,
            "label": f"Latest ({latest})",
        },
    )
    if style is None:
        return
    row = df.iloc[position]
    axes.scatter([row.iloc[0]], [row.iloc[1]], **style)


# --- public functions
def scatter_plot(data: DataFrame, **kwargs: Unpack[ScatterKwargs]) -> Axes:
    """Plot the second column of a DataFrame (y) against the first (x).

    Args:
        data: DataFrame - exactly two numeric columns, x first and y second.
            The index is not plotted; it identifies the latest point.
        kwargs: ScatterKwargs - keyword arguments for the scatter plot

    The overlays - diagonal, fit and highlight_latest - each take True for the
    house style, or a dict of matplotlib arguments merged over the house style.
        diagonal         - the y = x line (dashed, labelled "45° (equal)")
        fit              - an OLS line of best fit, in the colour of the points
        highlight_latest - the point with the latest index value, as a star
    report_corr=True appends the correlation to the label, e.g. "GDP (r = 0.83)".

    To layer several groups (each with its own colour and fit line), make
    repeated calls with the same ax=, then call finalise_plot().

    Returns:
    - axes: Axes - the axes object for the plot

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=ScatterKwargs, caller=ME, **kwargs)

    # --- check and prepare the data
    df, kwargs_d = _constrain(_check_data(data), dict(kwargs))
    if kwargs_d.pop("dropna", True):
        df = df.dropna()

    # --- Let's plot
    axes, kwargs_d = get_axes(**kwargs_d)
    if df.empty or df.isna().all().all():
        # Note: finalise plot should ignore an empty axes object
        print(f"Warning: No data to plot in {ME}().")
        return axes

    x, y = df.iloc[:, 0], df.iloc[:, 1]
    points: dict[str, Any] = {
        "color": kwargs_d.get("color", get_color_list(1)[0]),
        "s": kwargs_d.get("size", DEFAULT_SIZE),
        "alpha": kwargs_d.get("alpha", DEFAULT_ALPHA),
        "marker": kwargs_d.get("marker", DEFAULT_MARKER),
        "zorder": kwargs_d.get("zorder", DEFAULT_POINTS_ZORDER),
    }
    label = _points_label(kwargs_d.get("label"), x, y, report_corr=bool(kwargs_d.get("report_corr")))
    axes.scatter(x, y, label=label, **points)

    # --- overlays
    _draw_fit(axes, x, y, kwargs_d.get("fit"), points["color"])
    _draw_latest(axes, df, kwargs_d.get("highlight_latest"), points)
    _draw_diagonal(axes, kwargs_d.get("diagonal"))  # last, so its range covers the points

    return axes
