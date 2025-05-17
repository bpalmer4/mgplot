"""
multi_plot.py
This module provides a function to create multiple plots,
with different starting points for the data in each plot.
"""

from typing import Callable, Iterable, Final
from pandas import Period

from mgplot.settings import DataT


def multi_plot(
    data: DataT,
    function: Callable,
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

    Raises ValueError if the start is not a None, Period nor an int.
    """

    tag: Final[str] = kwargs.get("tag", "")
    for i, start in enumerate(starts):
        if start is None:
            subset = data
        elif isinstance(start, Period):
            subset = data.loc[data.index >= start]
        elif isinstance(start, int):
            subset = data.iloc[start:]
        else:
            raise ValueError("start must be a Period or an int")

        this_tag = f"{tag}_{i}" if tag else str(i)
        kwargs["tag"] = this_tag
        function(subset, **kwargs)
