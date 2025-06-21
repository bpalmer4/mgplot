"""Plot and highlight the 'runs' in a series."""

from collections.abc import Sequence
from typing import NotRequired, Unpack

from matplotlib import patheffects as pe
from matplotlib.pyplot import Axes
from pandas import Series, concat

from mgplot.axis_utils import map_periodindex, set_labels
from mgplot.keyword_checking import (
    limit_kwargs,
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import check_clean_timeseries, constrain_data

# --- constants
ME = "run_plot"


class RunKwargs(LineKwargs):
    """Keyword arguments for the run_plot function."""

    threshold: NotRequired[float]
    highlight: NotRequired[str | Sequence[str]]
    direction: NotRequired[str]


# --- functions


def _identify_runs(
    series: Series,
    threshold: float,
    *,
    up: bool,  # False means down
) -> tuple[Series, Series]:
    """Identify monotonic increasing/decreasing runs."""
    diffed = series.diff()
    change_points = concat([diffed[diffed.gt(threshold)], diffed[diffed.lt(-threshold)]]).sort_index()
    if series.index[0] not in change_points.index:
        starting_point = Series([0], index=[series.index[0]])
        change_points = concat([change_points, starting_point]).sort_index()
    facing = change_points > 0 if up else change_points < 0
    cycles = (facing & ~facing.shift().astype(bool)).cumsum()
    return cycles[facing], change_points


def _plot_runs(
    axes: Axes,
    series: Series,
    *,
    up: bool,
    **kwargs,
) -> None:
    """Highlight the runs of a series."""
    threshold = kwargs["threshold"]
    match kwargs.get("highlight"):  # make sure highlight is a color string
        case str():
            highlight = kwargs.get("highlight")
        case Sequence():
            highlight = kwargs["highlight"][0] if up else kwargs["highlight"][1]
        case _:
            raise ValueError(
                f"Invalid type for highlight: {type(kwargs.get('highlight'))}. Expected str or Sequence.",
            )

    # highlight the runs
    stretches, change_points = _identify_runs(series, threshold, up=up)
    for k in range(1, stretches.max() + 1):
        stretch = stretches[stretches == k]
        axes.axvspan(
            stretch.index.min(),
            stretch.index.max(),
            color=highlight,
            zorder=-1,
        )
        space_above = series.max() - series[stretch.index].max()
        space_below = series[stretch.index].min() - series.min()
        y_pos, vert_align = (series.max(), "top") if space_above > space_below else (series.min(), "bottom")
        text = axes.text(
            x=stretch.index.min(),
            y=y_pos,
            s=(change_points[stretch.index].sum().round(kwargs["rounding"]).astype(str) + " pp"),
            va=vert_align,
            ha="left",
            fontsize="x-small",
            rotation=90,
        )
        text.set_path_effects([pe.withStroke(linewidth=5, foreground="w")])


def run_plot(data: DataT, **kwargs: Unpack[RunKwargs]) -> Axes:
    """Plot a series of percentage rates, highlighting the increasing runs.

    Arguments:
        data: Series - ordered pandas Series of percentages, with PeriodIndex.
        kwargs: RunKwargs - keyword arguments for the run_plot function.

    Return:
     - matplotlib Axes object

    """
    # --- check the kwargs
    report_kwargs(caller="run_plot", **kwargs)
    validate_kwargs(schema=RunKwargs, caller=ME, **kwargs)

    # --- check the data
    series = check_clean_timeseries(data, ME)
    if not isinstance(series, Series):
        raise TypeError("series must be a pandas Series for run_plot()")
    series, kwargs_d = constrain_data(series, **kwargs)

    # --- convert PeriodIndex if needed
    saved_pi = map_periodindex(series)
    if saved_pi is not None:
        series = saved_pi[0]

    # --- default arguments - in **kwargs_d
    kwargs_d["threshold"] = kwargs_d.get("threshold", 0.1)
    kwargs_d["direction"] = kwargs_d.get("direction", "both")
    kwargs_d["rounding"] = kwargs_d.get("rounding", 2)
    kwargs_d["highlight"] = kwargs_d.get(
        "highlight",
        (
            ("gold", "skyblue")
            if kwargs_d["direction"] == "both"
            else "gold"
            if kwargs_d["direction"] == "up"
            else "skyblue"
        ),
    )
    kwargs_d["color"] = kwargs_d.get("color", "darkblue")

    # --- plot the line
    kwargs_d["drawstyle"] = kwargs_d.get("drawstyle", "steps-post")
    lp_kwargs = limit_kwargs(LineKwargs, **kwargs_d)
    axes = line_plot(series, **lp_kwargs)

    # plot the runs
    match kwargs["direction"]:
        case "up":
            _plot_runs(axes, series, up=True, **kwargs_d)
        case "down":
            _plot_runs(axes, series, up=False, **kwargs_d)
        case "both":
            _plot_runs(axes, series, up=True, **kwargs_d)
            _plot_runs(axes, series, up=False, **kwargs_d)
        case _:
            raise ValueError(
                f"Invalid value for direction: {kwargs['direction']}. Expected 'up', 'down', or 'both'.",
            )

    # --- set the labels
    if saved_pi is not None:
        set_labels(axes, saved_pi[1], kwargs.get("max_ticks", get_setting("max_ticks")))

    return axes
