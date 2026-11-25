"""Plot open-high-low-close candles, with no space for closed hours, weekends or holidays.

Each bar takes one slot on the x-axis (bar i at x = i), so only traded time is shown. A light
grey line marks each session boundary: wherever the time from one bar to the next is longer
than a bar (overnight and weekends for intraday bars, weekends and holidays for daily bars,
and gaps in the data). There are no x-gridlines, so every vertical line is a boundary. A
chart with more than max_boundaries boundaries (default 50: years of daily bars) gets none.

A series built on the chart's own bars (a moving average of the closes, say) can be layered
on with line_plot(), bar_plot() or fill_between_plot() and ax=; they place each point on its
bar. Data with any period that is not one of the bars raises a ValueError rather than being
drawn in the wrong place. share_bars() makes a second axes a panel on the same bars, for an
indicator drawn under the candles (MACD, volume).
"""

from collections.abc import Callable, Mapping
from typing import Any, Final, NotRequired, Unpack

from matplotlib.axes import Axes
from pandas import DataFrame, PeriodIndex

from mgplot.axis_utils import get_bar_axes, register_bar_axes, set_labels
from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting
from mgplot.utilities import constrain_data, get_axes

# --- constants
ME: Final[str] = "ohlc_plot"
OHLC_COLUMNS: Final[tuple[str, ...]] = ("Open", "High", "Low", "Close")
DEFAULT_UP_COLOR: Final[str] = "#2ca02c"  # green: closed at or above the open
DEFAULT_DOWN_COLOR: Final[str] = "#d62728"  # red: closed below the open
DEFAULT_BODY_WIDTH: Final[float] = 0.6  # share of a bar's slot
DEFAULT_WICK_WIDTH: Final[float] = 0.75  # points
BODY_EDGE_WIDTH: Final[float] = 0.5  # points: keeps a bar that closed at its open visible
DEFAULT_BOUNDARY_COLOR: Final[str] = "lightgrey"
DEFAULT_BOUNDARY_WIDTH: Final[float] = 0.75  # points
BOUNDARY_OFFSET: Final[float] = 0.5  # a boundary line sits midway between two bars
BOUNDARY_ZORDER: Final[float] = 1.0  # above the y-grid, below the candles
DEFAULT_MAX_BOUNDARIES: Final[int] = 50  # more boundaries than this, and none are drawn
CANDLE_ZORDER: Final[float] = 2.0


class BoundaryKwargs(BaseKwargs):
    """Keyword arguments for the session boundaries of an OHLC chart or a panel sharing its bars."""

    boundaries: NotRequired[bool]
    boundary_color: NotRequired[str]
    boundary_width: NotRequired[float]
    max_boundaries: NotRequired[int]


class OhlcKwargs(BoundaryKwargs):
    """Keyword arguments for the ohlc_plot function."""

    ax: NotRequired[Axes | None]
    up_color: NotRequired[str]
    down_color: NotRequired[str]
    body_width: NotRequired[float]
    wick_width: NotRequired[float]
    plot_from: NotRequired[int | None]
    max_ticks: NotRequired[int]
    tick_relabel: NotRequired[Callable[[str], str]]


def _prepare_bar_axes(axes: Axes, bars: PeriodIndex, kwargs_d: Mapping[str, Any]) -> None:
    """Record the bars on the axes, turn off its x-gridlines and draw its session boundaries.

    A boundary falls where the next bar starts later than this bar ends. On a long chart (years
    of daily bars, a line every weekend) they would hide the candles, so above max_boundaries
    none are drawn.
    """
    register_bar_axes(axes, bars)
    axes.grid(visible=False, axis="x")  # the only vertical lines are the session boundaries
    starts = bars.start_time
    follows = (bars + 1).start_time  # when the next bar would start with no gap
    gaps = [i for i in range(1, len(bars)) if starts[i] > follows[i - 1]]
    max_boundaries = kwargs_d.get("max_boundaries", DEFAULT_MAX_BOUNDARIES)
    if kwargs_d.get("boundaries", True) and len(gaps) <= max_boundaries:
        for i in gaps:
            axes.axvline(
                i - BOUNDARY_OFFSET,
                color=kwargs_d.get("boundary_color", DEFAULT_BOUNDARY_COLOR),
                linewidth=kwargs_d.get("boundary_width", DEFAULT_BOUNDARY_WIDTH),
                zorder=BOUNDARY_ZORDER,
            )


def share_bars(axes: Axes, ohlc_axes: Axes, **kwargs: Unpack[BoundaryKwargs]) -> Axes:
    """Make axes a panel on an OHLC chart's bars, such as an indicator under the candles.

    The panel gets the chart's bars (so line_plot(), bar_plot() and fill_between_plot() with
    ax= place each point on its bar, and refuse data that is not on the bars), the same session
    boundaries, and no x-gridlines. Create the two axes with a shared x-axis (for example
    plt.subplots(2, 1, sharex=True)) so the panels scroll and label together.

    Args:
        axes: Axes - the panel, which must not already hold a chart.
        ohlc_axes: Axes - an axes drawn by ohlc_plot().
        kwargs: BoundaryKwargs - how the panel's session boundaries are drawn.

    Returns:
        Axes - the panel.

    Raises:
        ValueError: If ohlc_axes holds no OHLC chart, or axes already holds a chart.

    """
    validate_kwargs(schema=BoundaryKwargs, caller="share_bars", **kwargs)
    bars = get_bar_axes(ohlc_axes)
    if bars is None:
        raise ValueError("share_bars: ohlc_axes holds no OHLC chart")
    _prepare_bar_axes(axes, bars, kwargs)
    return axes


def ohlc_plot(data: DataFrame, **kwargs: Unpack[OhlcKwargs]) -> Axes:
    """Plot candles from Open, High, Low and Close columns on a PeriodIndex.

    Args:
        data: DataFrame - Open, High, Low and Close columns (others are ignored) on a unique,
              increasing PeriodIndex of any frequency. Rows missing any of the four are dropped.
        kwargs: OhlcKwargs - keyword arguments for the plot.

    Returns:
        Axes - the matplotlib Axes, which must not already hold a chart.

    Raises:
        TypeError: If data is not a DataFrame on a PeriodIndex.
        ValueError: If a column is missing, the index is not unique and increasing, no row is
            complete, or the axes already holds a chart.

    """
    # --- validate inputs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=OhlcKwargs, caller=ME, **kwargs)
    if not isinstance(data, DataFrame):
        raise TypeError(f"data must be a DataFrame for {ME}()")
    missing = [column for column in OHLC_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"data for {ME}() lacks the column(s) {', '.join(missing)}")
    if not isinstance(data.index, PeriodIndex):
        raise TypeError(f"data for {ME}() must have a PeriodIndex")
    if not data.index.is_unique or not data.index.is_monotonic_increasing:
        raise ValueError(f"the index of data for {ME}() must be unique and increasing")

    # --- the bars: complete rows only, as a candle needs all four prices
    ohlc = data[list(OHLC_COLUMNS)].dropna()
    ohlc, kwargs_d = constrain_data(ohlc, **kwargs)
    if ohlc.empty:
        raise ValueError(f"no complete open-high-low-close rows to plot in {ME}()")
    bars = PeriodIndex(ohlc.index)
    axes, kwargs_d = get_axes(**kwargs_d)
    _prepare_bar_axes(axes, bars, kwargs_d)
    x = list(range(len(bars)))

    # --- candles: a wick from low to high, a body from open to close
    up = ohlc["Close"] >= ohlc["Open"]
    colors = [
        kwargs_d.get("up_color", DEFAULT_UP_COLOR) if rose else kwargs_d.get("down_color", DEFAULT_DOWN_COLOR)
        for rose in up
    ]
    axes.vlines(
        x,
        ohlc["Low"],
        ohlc["High"],
        colors=colors,
        linewidth=kwargs_d.get("wick_width", DEFAULT_WICK_WIDTH),
        zorder=CANDLE_ZORDER,
    )
    bodies = axes.bar(
        x,
        (ohlc["Close"] - ohlc["Open"]).abs(),
        bottom=ohlc[["Open", "Close"]].min(axis=1),
        width=kwargs_d.get("body_width", DEFAULT_BODY_WIDTH),
        color=colors,
        edgecolor=colors,
        linewidth=BODY_EDGE_WIDTH,
        zorder=CANDLE_ZORDER,
        label="_candles",
    )
    for body in bodies:  # a bar's base is sticky, and would stop the y-margin at a low close
        body.sticky_edges.y.clear()

    # --- tick labels from the bars
    set_labels(
        axes,
        bars,
        kwargs_d.get("max_ticks", get_setting("max_ticks")),
        tick_relabel=kwargs_d.get("tick_relabel"),
    )
    return axes
