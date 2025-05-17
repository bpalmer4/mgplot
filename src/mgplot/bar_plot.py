"""
bar_plot.py
This module contains functions to create bar plots using Matplotlib.
Note: bar plots in Matplotlib are not the same as bar charts in other
libraries. Bar plots are used to represent categorical data with
rectangular bars. As a result, bar plots and line plots typically
cannot be plotted on the same axes.
"""

# --- imports
from typing import Any
from pandas import Series, DataFrame, PeriodIndex, period_range
from numpy import random
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes

from mgplot.settings import DataT, get_setting
from mgplot.test import prepare_for_test
from mgplot.utilities import apply_defaults, get_color_list, get_axes
from mgplot.finalise_plot import finalise_plot, get_finalise_kwargs_list
from mgplot.date_utils import set_labels


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
        - bar_legend: bool - If True, show the legend [defaults to True].
        - "max_ticks": int - The maximum number of ticks on the x-axis,
          (this option only applies to PeriodIndex data.).

    Returns
    - axes: Axes - The axes for the plot.
    """

    # --- get the data
    df = DataFrame(data)  # really we are only plotting DataFrames
    item_count = len(df.columns)

    defaults: dict[str, Any] = {
        "color": get_color_list(item_count),
        "width": get_setting("bar_width"),
        "stacked": False,
        "rotation": 90,
        "bar_legend": True,
        "max_ticks": 10,
    }
    bar_args, remaining_kwargs = apply_defaults(item_count, defaults, kwargs)

    # --- plot the data
    axes, _rkwargs = get_axes(remaining_kwargs)

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


def bar_plot_finalise(
    data: DataT,
    **kwargs,
) -> None:
    """Build and finalise a bar plot. This function is a wrapper around
    the bar_plot function and finalise_plot function. It allows for
    additional customisation of the plot, such as setting the title,
    x-axis label, y-axis label, and other parameters.

    Parameters
    - data: Series - The data to plot. Can be a DataFrame or a Series.
    - **kwargs: dict Additional keyword arguments for customization,
      taking the same parameters as bar_plot and finalise_plot.
    """

    axes = bar_plot(data, **kwargs)
    fp_kwargs = {k: v for k, v in kwargs.items() if k in get_finalise_kwargs_list()}
    finalise_plot(
        axes,
        **fp_kwargs,
    )


# --- test ---
if __name__ == "__main__":
    # set the chart directory
    prepare_for_test("bar_plot")

    # Test 1
    series_ = Series([1, 2, 3, 4, 5], index=list("ABCDE"))
    ax = bar_plot(series_, rotation=45, bar_legend=False)
    finalise_plot(
        ax,
        title="Bar Plot Example 1",
        xlabel="X-axis Label",
        ylabel="Y-axis Label",
    )

    # Test 2
    df_ = DataFrame(
        {
            "Series 1": [1, 2, 3, 4, 5],
            "Series 2": [-5, -4, -3, -2, -1],
            "Series 3": [1, -1, -1, 1, -1],
        },
        index=list("ABCDE"),
    )
    ax = bar_plot(df_, stacked=True, rotation=0)
    finalise_plot(
        ax,
        title="Bar Plot Example 2a",
        xlabel="X-axis Label",
        ylabel="Y-axis Label",
        y0=True,
    )
    ax = bar_plot(df_, stacked=False, rotation=0)
    finalise_plot(
        ax,
        title="Bar Plot Example 2b",
        xlabel="X-axis Label",
        ylabel="Y-axis Label",
        y0=True,
    )

    # Test 3
    N = 25
    dates = period_range("2020-Q1", periods=N, freq="Q")
    series = Series(random.random(N), index=dates)
    bar_plot_finalise(
        series,
        title="Bar Plot Example 3",
        xlabel=None,
        ylabel="Y-axis Label",
        rfooter="Fake quarterly data",
        bar_legend=False,
    )
