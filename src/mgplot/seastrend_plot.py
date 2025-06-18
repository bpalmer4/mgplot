"""
seas_trend_plot.py
This module contains a function to create seasonal+trend plots.
It is just a light-weight wrapper around line_plot().
"""

# --- imports
from typing import Final, Unpack
from matplotlib.pyplot import Axes

from mgplot.settings import DataT
from mgplot.line_plot import line_plot, LineKwargs
from mgplot.utilities import get_color_list, get_setting, check_clean_timeseries
from mgplot.keyword_checking import report_kwargs, validate_kwargs

# --- constants
ME: Final[str] = "seastrend_plot"


# --- public functions
def seastrend_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """
    Publish a DataFrame, where the first column is seasonally
    adjusted data, and the second column is trend data.

    Aguments:
    - data: DataFrame - the data to plot with the first column
      being the seasonally adjusted data, and the second column
      being the trend data.
    The remaining arguments are the same as those passed to
    line_plot().

    Returns:
    - a matplotlib Axes object
    """

    # Note: we will rely on the line_plot() function to do most of the work.
    # including constraining the data to the plot_from keyword argument.

    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=LineKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
    if len(data.columns) < 2:
        raise ValueError("seas_trend_plot() expects a DataFrame data item with at least 2 columns.")

    # --- defaults if not in kwargs
    kwargs["color"] = kwargs.get("color", get_color_list(2))
    kwargs["width"] = kwargs.get("width", [get_setting("line_normal"), get_setting("line_wide")])
    kwargs["style"] = kwargs.get("style", ["-", "-"])
    kwargs["annotate"] = kwargs.get("annotate", [True, False])
    kwargs["rounding"] = kwargs.get("rounding", True)

    # series breaks are common in seas-trend data
    kwargs["dropna"] = kwargs.get("dropna", False)

    axes = line_plot(
        data,
        **kwargs,
    )

    return axes
