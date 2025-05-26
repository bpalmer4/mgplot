"""
multi_plot.py

This module provides a function to create multiple plots
from a single dataset:
- multi_start()
- multi_column()

And to chain a plotting function with the finalise_plot() function.
- plot_then_finalise()

Underlying assumptions:
- every plot function:
    - has a mandatory data: DataFrame | Series argument first (noting
      that some plotting functions only work with Series data, and they
      will raise an error if they are passed a DataFrame).
    - accepts an optional plot_from: int | Period keyword argument
    - accepts an optional plot_to: int | Period keyword argument
    - returns a matplotlib Axes object
- the multi functions (including plot_finalise)
    - have a mandatory data: DataFrame | Series argument
    - have a mandatory function: Callable | list[Callable] argument
    - the multi functions can be chained together. However, the
      plot_finalise() function must be the last function in a chain
      as it is designed to call a plot function and then the
      finalise_plot() function [and not another multi function].
    - return None.
"""

# --- imports
from typing import Any, Callable, Final
from collections.abc import Iterable
from pandas import Period, DataFrame, Series, period_range
from numpy import random

from mgplot.kw_type_checking import limit_kwargs, ExpectedTypeDict, validate_kwargs
from mgplot.finalise_plot import finalise_plot, FINALISE_KW_TYPES
from mgplot.settings import DataT
from mgplot.test import prepare_for_test

from mgplot.line_plot import line_plot, LP_KW_TYPES
from mgplot.bar_plot import bar_plot, BAR_PLOT_KW_TYPES
from mgplot.seastrend_plot import seastrend_plot
from mgplot.postcovid_plot import postcovid_plot
from mgplot.revision_plot import revision_plot, REVISION_KW_TYPES
from mgplot.run_plot import run_plot, RUN_KW_TYPES
from mgplot.summary_plot import summary_plot, SUMMARY_KW_TYPES
from mgplot.growth_plot import series_growth_plot, raw_growth_plot, GROWTH_KW_TYPES


# --- constants
EXPECTED_CALLABLES: Final[dict[Callable, ExpectedTypeDict]] = {
    line_plot: LP_KW_TYPES,
    bar_plot: BAR_PLOT_KW_TYPES,
    seastrend_plot: LP_KW_TYPES,  # just calls line_plot under the hood
    postcovid_plot: LP_KW_TYPES,  # just calls line_plot under the hood
    revision_plot: LP_KW_TYPES | REVISION_KW_TYPES,
    run_plot: LP_KW_TYPES | RUN_KW_TYPES,
    summary_plot: SUMMARY_KW_TYPES,
    series_growth_plot: GROWTH_KW_TYPES,
    raw_growth_plot: GROWTH_KW_TYPES,
}


# --- private functions
def first_unchain(
    function: Callable | list[Callable],
    kwargs: dict[str, Any],
) -> tuple[Callable, dict[str, Any]]:
    """
    Extract the first Callable from function (which may be
    a stand alone Callable or a nonr-empty list of Callables).
    Store the remaining Callables in kwargs['function'].
    This allows for chaining multiple functions together.

    Parameters
    - kwargs: dict[str, Any] - keyword arguments

    Returns a tuple containing the first function and the updated kwargs.
    if function is a list of Callables, the first function will be removed
    from the the list, and the remaining functions will be stored in a
    list under the key "function" in kwargs.

    Raises ValueError if function is an empty list.

    Not intended for direct use by the user.
    """

    error_msg = "function must be a Callable or a non-empty list of Callables"

    if isinstance(function, list):
        if len(function) == 0:
            raise ValueError(error_msg)
        first, rest = function[0], function[1:]
    elif callable(function):
        first, rest = function, []
    else:
        raise ValueError(error_msg)

    if rest:
        kwargs["function"] = rest

    return first, kwargs


# --- public functions
def plot_then_finalise(
    data: DataT,
    function: Callable | list[Callable],
    **kwargs,
) -> None:
    """
    Chain a plotting function with the finalise_plot() function.
    This is designed to be the last function in a chain.

    Parameters
    - data: Series | DataFrame - The data to be plotted.
    - function: Callable | list[Callable] - The plotting function
      to be used.
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function, and then the finalise_plot() function.

    Returns None.
    """

    first, kwargs_ = first_unchain(function, kwargs.copy())

    if first in EXPECTED_CALLABLES:

        expected = EXPECTED_CALLABLES[first]
        plot_kwargs = limit_kwargs(kwargs_.copy(), expected)
        expected |= FINALISE_KW_TYPES
        validate_kwargs(plot_kwargs, expected, "plot_then_finalise")
    else:
        # this is an unexpected Callable, so we will give it a try
        print(f"Unknown proposed function: {first}; nonetheless, will give it a try.")
        plot_kwargs = kwargs_

    axes = first(data, **plot_kwargs)

    fp_kwargs = limit_kwargs(kwargs_.copy(), FINALISE_KW_TYPES)
    finalise_plot(axes, **fp_kwargs)


def multi_start(
    data: DataT,
    function: Callable | list[Callable],
    starts: Iterable[None | Period | int],
    **kwargs,
) -> None:
    """
    Create multiple plots with different starting points.
    Each plot will start from the specified starting point.

    Parameters
    - data: Series | DataFrame - The data to be plotted.
    - function: Callable | list[Callable] - The plotting function
      to be used.
    - starts: Iterable[Period | int | None] - The starting points
      for each plot (None means use the entire data).
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function.

    Returns None.

    Raises
    - ValueError if the starts is not an iterable of None, Period or int.

    Note: kwargs['tag'] is used to create a unique tag for each plot.
    """

    if not isinstance(starts, Iterable):
        raise ValueError("starts must be an iterable of None, Period or int")

    tag: Final[str] = kwargs.get("tag", "")
    first, kwargs = first_unchain(function, kwargs)

    for i, start in enumerate(starts):
        kw = kwargs.copy()  # copy to avoid modifying the original kwargs
        this_tag = f"{tag}_{i}"
        kw["tag"] = this_tag
        kw["plot_from"] = start  # rely on plotting function to constrain the data
        first(data, **kw)


def multi_column(
    data: DataFrame,
    function: Callable | list[Callable],
    **kwargs,
) -> None:
    """
    Create multiple plots, one for each column in a DataFrame.
    The plot title will be the column name.

    Parameters
    - data: DataFrame - The data to be plotted.
    - function: Callable - The plotting function to be used.
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function.

    Returns None.
    """

    if not isinstance(data, DataFrame):
        raise ValueError("data must be a DataFrame")

    title_stem = kwargs.get("title", "")
    tag: Final[str] = kwargs.get("tag", "")
    first, kwargs = first_unchain(function, kwargs)

    for i, col in enumerate(data.columns):

        series = data[[col]]
        kwargs["title"] = f"{title_stem}{col}" if title_stem else col

        this_tag = f"_{tag}_{i}".replace("__", "_")
        kwargs["tag"] = this_tag

        first(series, **kwargs)


# --- test
if __name__ == "__main__":

    prepare_for_test("multi_plot")

    dates = period_range("2020-01-01", "2020-12-31", freq="D")
    df = DataFrame(
        {
            "Series 1": random.rand(len(dates)),
            "Series 2": random.rand(len(dates)),
            "Series 3": random.rand(len(dates)),
        },
        index=dates,
    )

    # Test multi_start
    multi_start(
        df,
        function=[plot_then_finalise, line_plot],
        starts=[None, 50, 100, Period("2020-06-01", freq="D")],
        title="Test Multi Start: ",
        tag="tag_test",
    )

    # Test multi_column
    multi_column(
        df, function=[plot_then_finalise, line_plot], title="Test Multi Column: "
    )

    # Test Test Multi Column / Multi start
    multi_column(
        df,
        [multi_start, plot_then_finalise, line_plot],
        title="Test Multi Column / Multi start: ",
        starts=[None, 180],
        verbose=False,
    )

    # bar plot
    # Test 1
    series_ = Series([1, 2, 3, 4, 5], index=list("ABCDE"))
    plot_then_finalise(
        series_,
        function=bar_plot,
        title="Bar Plot Example 1a",
        xlabel="X-axis Label",
        ylabel="Y-axis Label",
        rotation=45,
    )
    multi_start(
        series_,
        function=[plot_then_finalise, bar_plot],
        starts=[0, -2],
        title="Multi-start Bar Plot Example 1b",
        xlabel="X-axis Label",
        ylabel="Y-axis Label",
    )
