"""Plot ABS revisions to estimates over time."""

from typing import Unpack

from matplotlib.pyplot import Axes
from pandas import DataFrame

from mgplot.keyword_checking import report_kwargs, validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries

# --- constants
ME = "revision_plot"


# --- functions
def revision_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """Plot the revisions to ABS data.

    Args:
        data: DataFrame - the data to plot, with a column for each data revision
        kwargs: LineKwargs - additional keyword arguments for the line_plot function.

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
    return line_plot(data, **kwargs)
