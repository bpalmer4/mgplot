"""
run_plot.py
This code contains a function to plot and highlighted
the 'runs' in a series.
"""

# --- imports
from collections.abc import Sequence
from pandas import Series, concat, period_range
from matplotlib.pyplot import Axes
from matplotlib import patheffects as pe

from mgplot.settings import DataT
from mgplot.line_plot import line_plot, LINE_KW_TYPES
from mgplot.kw_type_checking import (
    limit_kwargs,
    ExpectedTypeDict,
    validate_kwargs,
    validate_expected,
    report_kwargs,
)
from mgplot.utilities import constrain_data, check_clean_timeseries


# --- constants
THRESHOLD = "threshold"
ROUND = "round"
HIGHLIGHT = "highlight"
DIRECTION = "direction"

RUN_KW_TYPES: ExpectedTypeDict = {
    THRESHOLD: float,
    ROUND: int,
    HIGHLIGHT: (str, Sequence, (str,)),  # colors for highlighting the runs
    DIRECTION: str,  # "up", "down" or "both"
}
RUN_KW_TYPES |= LINE_KW_TYPES
validate_expected(RUN_KW_TYPES, "run_highlight_plot")

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
            fontsize="x-small",
            rotation=90,
        )
        text.set_path_effects([pe.withStroke(linewidth=5, foreground="w")])


def run_plot(data: DataT, **kwargs) -> Axes:
    """Plot a series of percentage rates, highlighting the increasing runs.

    Arguments
     - data - ordered pandas Series of percentages, with PeriodIndex
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

    # --- check the kwargs
    me = "run_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(RUN_KW_TYPES, me, **kwargs)

    # --- check the data
    series = check_clean_timeseries(data, me)
    if not isinstance(series, Series):
        raise TypeError("series must be a pandas Series for run_plot()")
    series, kwargs = constrain_data(series, **kwargs)

    # --- default arguments - in **kwargs
    kwargs[THRESHOLD] = kwargs.get(THRESHOLD, 0.1)
    kwargs[ROUND] = kwargs.get(ROUND, 2)
    direct = kwargs[DIRECTION] = kwargs.get(DIRECTION, "up")
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
    lp_kwargs = limit_kwargs(LINE_KW_TYPES, **kwargs)
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


# test ---
if __name__ == "__main__":
    N_PERIODS = 25
    periods = period_range(start="2020Q1", periods=N_PERIODS, freq="Q")
    dataset = Series([1] * N_PERIODS, index=periods).cumsum()

    ax = run_plot(data=dataset, junk="should generate a warning")
