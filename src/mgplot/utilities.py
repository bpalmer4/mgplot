"""
utilities.py:
Utiltiy functions used by more than one mgplot module.
These are not intended to be used directly by the user.
"""

# --- imports
from typing import Any
from matplotlib import cm
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
            multiplier = (length // len(returnable[option])) + 1
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
    return [
        f"#{int(x*255):02x}{int(y*255):02x}{int(z*255):02x}" for x, y, z, _ in c
    ]
