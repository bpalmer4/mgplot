"""
multi_plot.py
This module provides a function to create multiple plots,
with different starting points for the data in each plot.
"""

from typing import Any, Callable, Final
from collections.abc import Iterable
from pandas import Period, DataFrame, period_range
from numpy import random

from mgplot.settings import DataT
from mgplot.line_plot import line_plot_finalise
from mgplot.test import prepare_for_test


def _f_chain(
    function: Callable | list[Callable],
    kwargs: dict[str, Any],
) -> tuple[Callable, dict[str, Any]]:
    """
    Extract the first function from a list of functions.
    Store the remaining functions in kwargs['function'].
    This allows for chaining multiple functions together.

    Parameters
    - function: Callable | list[Callable] - The function or list of functions.
    - kwargs: dict[str, Any] - Additional keyword arguments.

    Returns a tuple containing the first function and the updated kwargs.
    """

    if isinstance(function, list):
        first, rest = function[0], function[1:]
    else:
        first, rest = function, []

    if rest:
        kwargs["function"] = rest

    return first, kwargs


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
    - function: Callable - The plotting function to be used.
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
    first, kwargs = _f_chain(function, kwargs)

    for i, start in enumerate(starts):
        if start is None:
            subset = data
        elif isinstance(start, Period):
            subset = data.loc[data.index >= start]
        elif isinstance(start, int):
            subset = data.iloc[start:]
        else:
            raise ValueError("start must be a Period or an int")

        this_tag = f"_{tag}_{i}".replace("__", "_")
        kwargs["tag"] = this_tag

        first(subset, **kwargs)


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
    first, kwargs = _f_chain(function, kwargs)

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
        function=line_plot_finalise,
        starts=[None, 50, 100, Period("2020-06-01", freq="D")],
        title="Test Multi Start: ",
        tag="tag_test",
    )

    # Test multi_column
    multi_column(
        df,
        function=line_plot_finalise,
        title="Test Multi Column: ",
    )

    # Test Test Multi Column / Multi start
    multi_column(
        df,
        function=[multi_start, line_plot_finalise],
        title="Test Multi Column / Multi start: ",
        starts=[None, 180],
        verbose=False,
    )
