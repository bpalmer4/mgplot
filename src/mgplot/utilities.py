"""
utilities.py:
Utiltiy functions used by more than one mgplot module.
These are not intended to be used directly by the user.
"""

# --- imports
import math
from typing import Any
from matplotlib import cm
from matplotlib.pyplot import Axes, subplots
from pandas import Series
import numpy as np
from mgplot.settings import get_setting


# --- functions
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


def get_axes(kwargs: dict[str, Any]) -> tuple[Axes, dict[str, Any]]:
    """Get the axes to plot on.
    If not passed in kwargs, create a new figure and axes."""

    ax = "ax"
    if ax in kwargs and kwargs[ax] is not None:
        axes: Axes = kwargs[ax]
        if not isinstance(axes, Axes):
            raise TypeError("The ax argument must be a matplotlib Axes object")
        return axes, {}

    figsize = kwargs.pop("figsize", get_setting("figsize"))
    _fig, axes = subplots(figsize=figsize)
    return axes, kwargs


def annotate_series(
    series: Series,
    axes: Axes,
    rounding: int | bool = False,
    color: str = "#444444",
    fontsize: int | str = "small",
    **kwargs,
) -> None:
    """Annotate the right-hand end-point of a line-plotted series."""

    latest = series.dropna()
    if latest.empty:
        return

    x, y = latest.index[-1], latest.iloc[-1]
    if y is None or math.isnan(y):
        return

    r_string = f" {y}"  # default to no rounding
    original = rounding
    if isinstance(rounding, bool) and rounding:
        rounding = 0 if y >= 100 else 1 if y >= 10 else 2
    if not isinstance(rounding, bool) and isinstance(rounding, int):
        r_string = f" {y:.{rounding}f}"

    if "test" in kwargs:
        print(f"annotate_series: {x=}, {y=}, {original=} {rounding=} {r_string=}")
        return

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


# ---- kwargs management


# def report_bad_kwargs(
#    kwargs: dict[str, Any],
#    kwarg_list: list[str] | tuple[str] | set[str] | frozenset[str],
#    called_from: str = "",
# ) -> None:
#    """Report any bad keyword arguments passed to a function."""#
#
#    called_from = f"{called_from} " if called_from else ""
#
#    bad_kwargs = [k for k in kwargs if k not in kwarg_list]
#    if bad_kwargs:
#        print(
#            f"Warning: {called_from}" + f"got unknown keyword arguments: {bad_kwargs}"
#        )


# --- test code
if __name__ == "__main__":

    # --- test annotate_series()
    axes_, _ = get_axes({})
    series_ = Series([1.12345, 2.12345, 3.12345, 4.12345, 5.12345])
    rounding_ = (
        False,
        True,
        0,
        1,
        2,
        3,
    )
    for r in rounding_:
        annotate_series(series_, axes_, rounding=r, test=True)
    print("Done")
