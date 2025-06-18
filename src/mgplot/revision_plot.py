"""
revision_plot.py

Plot ABS revisions to estimates over time.  This is largely
a wrapper around the line_plot function, with some
default settings and minimal checks on the data.
"""

# --- imports
from typing import Unpack
from matplotlib.pyplot import Axes
from pandas import DataFrame

from mgplot.utilities import check_clean_timeseries
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.keyword_checking import validate_kwargs, report_kwargs
from mgplot.settings import DataT


# --- constants
ME = "revision_plot"


# --- functions
def revision_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """
    Plot the revisions to ABS data.

    Arguments
    data: pd.DataFrame - the data to plot, the DataFrame has a
        column for each data revision
    kwargs - additional keyword arguments for the line_plot function.
    """

    # --- check the kwargs and data
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=LineKwargs, caller=ME, **kwargs)
    data = check_clean_timeseries(data, ME)

    # --- additional checks
    if not isinstance(data, DataFrame):
        print(f"{ME}() requires a DataFrame with columns for each revision, not a Series or any other type.")

    # --- critical defaults
    kwargs["plot_from"] = kwargs.get("plot_from", -15)
    kwargs["annotate"] = kwargs.get("annotate", True)
    kwargs["annotate_color"] = kwargs.get("annotate_color", "black")
    kwargs["rounding"] = kwargs.get("rounding", 3)

    # --- plot
    axes = line_plot(data, **kwargs)

    return axes
