"""
revision_plot.py

Plot ABS revisions to estimates over time.  This is largely
a wrapper around the line_plot function, with some
default settings and minimal checks on the data.
"""

# --- imports
from matplotlib.pyplot import Axes
from pandas import DataFrame

from mgplot.utilities import check_clean_timeseries
from mgplot.line_plot import LINE_KW_TYPES, line_plot
from mgplot.kw_type_checking import validate_kwargs, validate_expected
from mgplot.kw_type_checking import report_kwargs
from mgplot.settings import DataT
from mgplot.kw_type_checking import ExpectedTypeDict


# --- constants
REVISION_KW_TYPES: ExpectedTypeDict = LINE_KW_TYPES
validate_expected(REVISION_KW_TYPES, "revision_plot")


# --- functions
def revision_plot(data: DataT, **kwargs) -> Axes:
    """
    Plot the revisions to ABS data.

    Arguments
    data: pd.DataFrame - the data to plot, the DataFrame has a
        column for each data revision
    kwargs - additional keyword arguments for the line_plot function.
    """

    # --- check the kwargs and data
    me = "revision_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(REVISION_KW_TYPES, me, **kwargs)

    data = check_clean_timeseries(data, me)

    # --- additional checks
    if not isinstance(data, DataFrame):
        print(
            f"{me} requires a DataFrame with columns for each revision, "
            "not a Series or other type."
        )

    # --- critical defaults
    kwargs["plot_from"] = kwargs.get("plot_from", -15)
    kwargs["annotate"] = kwargs.get("annotate", True)
    kwargs["annotate_color"] = kwargs.get("annotate_color", "black")
    kwargs["rounding"] = kwargs.get("rounding", 3)

    # --- plot
    axes = line_plot(data, **kwargs)

    return axes
