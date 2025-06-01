"""
utilities.py:
Utiltiy functions used by more than one mgplot module.
These are not intended to be used directly by the user.

Functions:
- check_clean_timeseries()
- constrain_data()
- apply_defaults()
- get_color_list()
- get_axes()
- annotate_series()
"""

# --- imports
import math
from typing import Any
from pandas import Series, DataFrame, Period, PeriodIndex, period_range
import numpy as np
from matplotlib import cm
from matplotlib.pyplot import Axes, subplots

from mgplot.settings import get_setting
from mgplot.settings import DataT


# --- functions
def check_clean_timeseries(data: DataT, called_by: str) -> DataT:
    """
    Check timeseries data for the following:
    - That the data is a Series or DataFrame.
    - That the index is a PeriodIndex
    - That the index is unique and monotonic increasing

    Remove any leading NAN rows or columns from the data.

    Return the cleaned data.

    Args:
    - data: the data to be cleaned

    Returns:
    - The data with leading NaN values removed.

    Raises TypeError/Value if problems found
    """

    # --- initial checks
    if not isinstance(data, (Series, DataFrame)):
        raise TypeError("Data must be a pandas Series or DataFrame.")
    if not isinstance(data.index, PeriodIndex):
        raise TypeError("Data index must be a PeriodIndex.")
    if not data.index.is_unique:
        raise ValueError("Data index must be unique.")
    if not data.index.is_monotonic_increasing:
        raise ValueError("Data index must be monotonic increasing.")

    # --- remove any leading NaNs
    start = data.first_valid_index()
    if start is None:
        return data  # no valid index, return original data
    if not isinstance(start, Period):  # syntactic sugar for type hinting
        raise TypeError("First valid index must be a Period.")
    data = data.loc[data.index >= start]

    # --- report and missing periods (ie. potentially incomplete data)
    data_index = PeriodIndex(data.index)  # syntactic sugar for type hinting
    complete = period_range(
        start=data_index.min(), end=data_index.max(), freq=data_index.freq
    )
    missing = complete.difference(data_index)
    if not missing.empty:
        plural = "s" if len(missing) > 1 else ""
        print(
            f"Warning: {len(missing)} period{plural} missing from data index. "
            + f"Found by {called_by}."
        )

    # --- return the final data
    return data


def constrain_data(data: DataT, **kwargs) -> tuple[DataT, dict[str, Any]]:
    """
    Constrain the data to start after a certain point - kwargs["plot_from"].

    Args:
        data: the data to be constrained
        kwargs: keyword arguments - uses "plot_from" in kwargs to constrain the data

    Assume:
    - that mgplot.utilitiesd.check_clean_timeseries() has already been applied
    - that the data is a Series or DataFrame with a PeriodIndex
    - that the index is unique and monotonic increasing

    Returns:
        A tuple of the constrained data and the modified kwargs.
    """

    plot_from = kwargs.pop("plot_from", 0)
    if isinstance(plot_from, Period) and isinstance(data.index, PeriodIndex):
        data = data.loc[data.index >= plot_from]
    elif isinstance(plot_from, int):
        data = data.iloc[plot_from:]
    elif plot_from is None:
        pass
    else:
        print(f"Warning: {plot_from=} either not a valid type or not applicable. ")
    return data, kwargs


def apply_defaults(
    length: int, defaults: dict[str, Any], kwargs_d: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, list[Any] | tuple[Any]]]:
    """
    Get arguments from kwargs_d, and apply a default from the
    defaults dict if not there. Remove the item from kwargs_d.

    Agumenets:
        length: the number of lines to be plotted
        defaults: a dictionary of default values
        kwargs_d: a dictionary of keyword arguments

    Returns a tuple of two dictionaries:
        - the first is a dictionary populated with the arguments
          from kwargs_d or the defaults dictionary, where the values
          are placed in lists or tuples if not already in that format
        - the second is a modified kwargs_d dictionary, with the default
          keys removed.
    """

    returnable = {}  # return vehicle

    for option, default in defaults.items():
        val = kwargs_d.get(option, default)
        # make sure our return value is a list/tuple
        returnable[option] = val if isinstance(val, (list, tuple)) else (val,)

        # remove the option from kwargs
        if option in kwargs_d:
            del kwargs_d[option]

        # repeat multi-item lists if not long enough for all lines to be plotted
        if len(returnable[option]) < length and length > 1:
            multiplier = math.ceil(length / len(returnable[option]))
            returnable[option] = returnable[option] * multiplier

    return returnable, kwargs_d


def get_color_list(count: int) -> list[str]:
    """
    Get a list of colours for plotting.

    Args:
        count: the number of colours to return

    Returns:
        A list of colours.
    """

    colors: dict[int, list[str]] = get_setting("colors")
    if count in colors:
        return colors[count]

    if count < max(colors.keys()):
        options = [k for k in colors.keys() if k > count]
        return colors[min(options)][:count]

    c = cm.get_cmap("nipy_spectral")(np.linspace(0, 1, count))
    return [f"#{int(x*255):02x}{int(y*255):02x}{int(z*255):02x}" for x, y, z, _ in c]


def get_axes(**kwargs) -> tuple[Axes, dict[str, Any]]:
    """
    Get the axes to plot on.
    If not passed in kwargs, create a new figure and axes.
    """

    ax = "ax"
    if ax in kwargs and kwargs[ax] is not None:
        axes: Axes = kwargs[ax]
        if not isinstance(axes, Axes):
            raise TypeError("The ax argument must be a matplotlib Axes object")
        return axes, {}

    figsize = kwargs.pop("figsize", get_setting("figsize"))
    _fig, axes = subplots(figsize=figsize)
    return axes, kwargs


def default_rounding(t: int | float) -> int:
    """Default rounding regime."""

    return 0 if t >= 100 else 1 if t >= 10 else 2


def annotate_series(
    series: Series,
    axes: Axes,
    **kwargs,  # "fontsize", "rounding",
) -> None:
    """Annotate the right-hand end-point of a line-plotted series."""

    # --- check the series has a value to annotate
    latest = series.dropna()
    if series.empty:
        return
    x, y = latest.index[-1], latest.iloc[-1]
    if y is None or math.isnan(y):
        return

    # --- extract fontsize - could be None, bool, int or str.
    fontsize = kwargs.get("fontsize", "small")
    if fontsize is None or isinstance(fontsize, bool):
        fontsize = "small"

    # --- extract rounding - could be None, bool or int
    rounding = default_rounding(y)  # the case for None or bool
    if "rounding" in kwargs:
        possible = kwargs["rounding"]
        if not isinstance(possible, bool):
            if isinstance(possible, int):
                rounding = possible

    # --- do the rounding
    r_string = f"  {int(y)}"  # default to no rounding
    if rounding > 0:
        r_string = f"  {y:.{rounding}f}"

    # --- add the annotation
    if "test" in kwargs and kwargs["test"]:
        print(f"annotate_series: {x=}, {y=}, {rounding=} {r_string=}")
        return

    color = kwargs.get("color", "black")
    axes.text(
        x=x,
        y=y,
        s=r_string,
        ha="left",
        va="center",
        fontsize=fontsize,
        color=color,
        font="Helvetica",
    )


# --- test code
if __name__ == "__main__":

    # --- test check_clean_timeseries_data()
    my_list = [np.nan, np.nan, 1.12345, 2.12345, 3.12345, 4.12345, 5.12345]
    _ = Series(my_list, period_range(start="2023-01", periods=len(my_list), freq="M"))
    _ = _.drop(index=[_.index[3]])
    clean = check_clean_timeseries(_, "test")
    print(f"Cleaned data:\n{clean}")

    # --- test annotate_series()
    print()
    _fig, ax_ = subplots(figsize=(9, 4.5))
    series2_ = Series([1.12345, 2.12345, 3.12345, 4.12345, 5.12345])
    rounding_ = (
        False,
        True,
        0,
        1,
        2,
        3,
    )
    for r in rounding_:
        annotate_series(series2_, ax_, rounding=r, test=True)
    print("Done")
