"""
bar_plot.py
This module contains functions to create bar plots using Matplotlib.
Note: bar plots in Matplotlib are not the same as bar charts in other
libraries. Bar plots are used to represent categorical data with
rectangular bars. As a result, bar plots and line plots typically
cannot be plotted on the same axes.
"""

# --- imports
from typing import Any, Final
from collections.abc import Sequence
from pandas import DataFrame, period_range, PeriodIndex
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes

from mgplot.settings import DataT, get_setting
from mgplot.utilities import apply_defaults, get_color_list, get_axes, constrain_data
from mgplot.kw_type_checking import (
    ExpectedTypeDict,
    validate_expected,
    report_kwargs,
    validate_kwargs,
)
from mgplot.date_utils import set_labels


# --- constants
BAR_KW_TYPES: Final[ExpectedTypeDict] = {
    "color": (str, Sequence, (str,)),
    "width": float,
    "stacked": bool,
    "rotation": (int, float),
    "bar_legend": bool,
    "max_ticks": int,
    "plot_from": (int, PeriodIndex, type(None)),
}
validate_expected(BAR_KW_TYPES, "bar_plot")


# --- functions
def bar_plot(
    data: DataT,
    **kwargs,
) -> Axes:
    """
    Create a bar plot from the given data. Each column in the DataFrame
    will be stacked on top of each other, with positive values above
    zero and negative values below zero.

    Parameters
    - data: Series - The data to plot. Can be a DataFrame or a Series.
    - **kwargs: dict Additional keyword arguments for customization.
        - color: list - A list of colors for the each series (column) in  the DataFrame.
        - width: float - The width of the bars.
        - stacked: bool - If True, the bars will be stacked.
        - rotation: int - The rotation angle in degrees for the x-axis labels.
        - bar_legend: bool - If True, show the legend. Defaults to True
          if more than one bar being plotted for each category.
        - "max_ticks": int - The maximum number of ticks on the x-axis,
          (this option only applies to PeriodIndex data.).

    Note: This function does not assume all data is timeseries with a PeriodIndex,

    Returns
    - axes: Axes - The axes for the plot.
    """

    # --- check the kwargs
    me = "bar_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(BAR_KW_TYPES, me, **kwargs)

    # --- get the data
    # no call to check_clean_timeseries here, as bar plots are not
    # necessarily timeseries data. If the data is a Series, it will be
    # converted to a DataFrame with a single column.
    df = DataFrame(data)  # really we are only plotting DataFrames
    df, kwargs = constrain_data(df, **kwargs)
    item_count = len(df.columns)

    defaults: dict[str, Any] = {
        "color": get_color_list(item_count),
        "width": get_setting("bar_width"),
        "stacked": False,
        "rotation": 90,
        "bar_legend": (item_count > 1),
        "max_ticks": 10,
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, defaults, kwargs)

    # --- plot the data
    axes, _rkwargs = get_axes(**remaining_kwargs)

    df.plot.bar(
        ax=axes,
        color=bar_args["color"],
        stacked=bar_args["stacked"][0],
        width=bar_args["width"][0],
        legend=bar_args["bar_legend"][0],
    )

    rotate_labels = True
    if isinstance(df.index, PeriodIndex):
        complete = period_range(
            start=df.index.min(), end=df.index.max(), freq=df.index.freqstr
        )
        if complete.equals(df.index):
            # if the index is complete, we can set the labels
            set_labels(axes, df.index, bar_args["max_ticks"][0])
            rotate_labels = False

    if rotate_labels:
        plt.xticks(rotation=bar_args["rotation"][0])

    return axes
