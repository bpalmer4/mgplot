"""
run_highlight_plot.py
This code contains a function to plot and highlighted
the 'runs' in a series.
"""

# --- imports
from collections.abc import Sequence
from pandas import Series, concat, period_range
from matplotlib.pyplot import Axes
from matplotlib import patheffects as pe

from mgplot.line_plot import line_plot
from mgplot.kw_type_checking import (
    limit_kwargs,
    ExpectedTypeDict,
    validate_kwargs,
    validate_expected,
)
from mgplot.line_plot import LP_KW_TYPES
from mgplot.test import prepare_for_test
from mgplot.finalise_plot import finalise_plot

# --- constants
THRESHOLD = "threshold"
ROUND = "round"
HIGHLIGHT = "highlight"
DIRECTION = "direction"

RH_KW_TYPES: ExpectedTypeDict = {
    THRESHOLD: float,
    ROUND: int,
    HIGHLIGHT: (str, Sequence, (str,)),  # colors for highlighting the runs
    DIRECTION: str,  # "up", "down" or "both"
}
validate_expected(RH_KW_TYPES, "run_highlight_plot")

# --- functions


def _identify_runs(
    series: Series,
    threshold: float,
    up: bool,  # False means down
) -> tuple[Series, Series]:
    """Identify monotonic increasing/decreasing runs."""

    diffed = series.diff()
    change_points = concat(
        [diffed[diffed.gt(threshold)], diffed[diffed.lt(-threshold)]]
    ).sort_index()
    if series.index[0] not in change_points.index:
        starting_point = Series([0], index=[series.index[0]])
        change_points = concat([change_points, starting_point]).sort_index()
    facing = change_points > 0 if up else change_points < 0
    cycles = (facing & ~facing.shift().astype(bool)).cumsum()
    return cycles[facing], change_points


def _plot_runs(
    axes: Axes,
    series: Series,
    up: bool,
    **kwargs,
) -> None:
    """Highlight the runs of a series."""

    threshold = kwargs[THRESHOLD]
    match kwargs.get(HIGHLIGHT):  # make sure highlight is a color string
        case str():
            highlight = kwargs.get(HIGHLIGHT)
        case Sequence():
            highlight = kwargs[HIGHLIGHT][0] if up else kwargs[HIGHLIGHT][1]
        case _:
            raise ValueError(
                f"Invalid type for highlight: {type(kwargs.get(HIGHLIGHT))}. "
                "Expected str or Sequence."
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
        y_pos, vert_align = (
            (series.max(), "top")
            if space_above > space_below
            else (series.min(), "bottom")
        )
        text = axes.text(
            x=stretch.index.min(),
            y=y_pos,
            s=(
                change_points[stretch.index].sum().round(kwargs["round"]).astype(str)
                + " pp"
            ),
            va=vert_align,
            ha="left",
            fontsize="small",
            rotation=90,
        )
        text.set_path_effects([pe.withStroke(linewidth=5, foreground="w")])


def run_highlight_plot(series: Series, **kwargs) -> Axes:
    """Plot a series of percentage rates, highlighting the increasing runs.

    Arguments
     - series - ordered pandas Series of percentages, with PeriodIndex
     - **kwargs
        - threshold - float - used to ignore micro noise near zero
          (for example, threshhold=0.01)
        - round - int - rounding for highlight text
        - highlight - str or Sequence[str] - color(s) for highlighting the
          runs, two colors can be specified in a list if direction is "both"
        - direction - str - whether the highlight is for an upward
          or downward or both runs. Options are "up", "down" or "both".
        - in addition the **kwargs for line_plot are accepted.

    Return
     - matplotlib Axes object"""

    # check the kwargs
    expected = RH_KW_TYPES | LP_KW_TYPES
    validate_kwargs(kwargs, expected, "run_highlight_plot")

    # default arguments - in **kwargs
    kwargs[THRESHOLD] = kwargs.get(THRESHOLD, 0.1)
    kwargs[ROUND] = kwargs.get(ROUND, 2)
    direct = kwargs[DIRECTION] = kwargs.get(DIRECTION, "up")

    # default line and highlight colors
    kwargs[HIGHLIGHT], kwargs["color"] = (
        (kwargs.get(HIGHLIGHT, "gold"), kwargs.get("color", "#dd0000"))
        if direct == "up"
        else (
            (kwargs.get(HIGHLIGHT, "skyblue"), kwargs.get("color", "navy"))
            if direct == "down"
            else (
                kwargs.get(HIGHLIGHT, ("gold", "skyblue")),
                kwargs.get("color", "navy"),
            )
        )
    )

    # defauls for line_plot
    kwargs["width"] = kwargs.get("width", 2)

    # plot the line
    kwargs["drawstyle"] = kwargs.get("drawstyle", "steps-post")
    lp_kwargs = limit_kwargs(kwargs, LP_KW_TYPES)
    axes = line_plot(series, **lp_kwargs)

    # plot the runs
    match kwargs[DIRECTION]:
        case "up":
            _plot_runs(axes, series, up=True, **kwargs)
        case "down":
            _plot_runs(axes, series, up=False, **kwargs)
        case "both":
            _plot_runs(axes, series, up=True, **kwargs)
            _plot_runs(axes, series, up=False, **kwargs)
        case _:
            raise ValueError(
                f"Invalid value for direction: {kwargs[DIRECTION]}. "
                "Expected 'up', 'down', or 'both'."
            )
    return axes


# --- test
if __name__ == "__main__":  # pragma: no cover          # pragma: no cover
    prepare_for_test("run_highlight_plot")

    data_ = [
        5.75,
        5.75,
        5.25,
        5.25,
        5.25,
        5.25,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        5.5,
        5.5,
        6.5,
        6.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.5,
        7.0,
        7.0,
        7.0,
        7.0,
        6.5,
        6.0,
        6.0,
        6.0,
        6.0,
        6.0,
        5.5,
        5.5,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        5.0,
        5.0,
        5.0,
        5.5,
        5.5,
        5.75,
        6.0,
        6.0,
        6.0,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        5.75,
        5.5,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        4.75,
        4.5,
        4.5,
        4.25,
        4.25,
        4.25,
        4.25,
        4.25,
        4.5,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        5.0,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.25,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.5,
        5.75,
        5.75,
        5.75,
        6.0,
        6.0,
        6.0,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.25,
        6.5,
        6.5,
        6.5,
        6.75,
        6.75,
        6.75,
        7.0,
        7.25,
        7.25,
        7.25,
        7.25,
        7.25,
        7.25,
        7.0,
        6.0,
        5.25,
        4.25,
        4.25,
        3.25,
        3.25,
        3.0,
        3.0,
        3.0,
        3.0,
        3.0,
        3.0,
        3.25,
        3.5,
        3.75,
        3.75,
        3.75,
        4.0,
        4.25,
        4.5,
        4.5,
        4.5,
        4.5,
        4.5,
        4.5,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.75,
        4.5,
        4.25,
        4.25,
        4.25,
        4.25,
        4.25,
        3.75,
        3.5,
        3.5,
        3.5,
        3.5,
        3.25,
        3.25,
        3.0,
        3.0,
        3.0,
        3.0,
        3.0,
        2.75,
        2.75,
        2.75,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.5,
        2.25,
        2.25,
        2.25,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        2.0,
        1.75,
        1.75,
        1.75,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.5,
        1.25,
        1.0,
        1.0,
        1.0,
        0.75,
        0.75,
        0.75,
        0.75,
        0.75,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.35,
        0.85,
        1.35,
        1.85,
        2.35,
        2.6,
        2.85,
        3.1,
        3.1,
        3.35,
        3.6,
        3.6,
        3.85,
        4.1,
        4.1,
        4.1,
        4.1,
        4.1,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.35,
        4.1,
        4.1,
        4.1,
        3.85,
    ]
    series_ = Series(data_, index=period_range("1993-01", periods=len(data_), freq="M"))
    ax = run_highlight_plot(series_, direction="up")
    finalise_plot(ax, title="UP Highlight Plot", xlabel=None, ylabel="Value")

    ax = run_highlight_plot(series_, direction="down")
    finalise_plot(ax, title="DOWN Highlight Plot", xlabel=None, ylabel="Value")

    ax = run_highlight_plot(series_, direction="both")
    finalise_plot(ax, title="BOTH Highlight Plot", xlabel=None, ylabel="Value")
