"""
revision_plot.py
Plot ABS revisions to estimates over time.
"""

# --- imports
from pandas import Series
from matplotlib.pyplot import Axes


from mgplot.utilities import annotate_series, check_clean_timeseries
from mgplot.line_plot import LINE_KW_TYPES, line_plot
from mgplot.kw_type_checking import validate_kwargs, validate_expected
from mgplot.kw_type_checking import report_kwargs
from mgplot.settings import DataT
from mgplot.kw_type_checking import ExpectedTypeDict


# --- constants
ROUNDING = "rounding"
REVISION_KW_TYPES: ExpectedTypeDict = {
    ROUNDING: (int, bool),
} | LINE_KW_TYPES
validate_expected(REVISION_KW_TYPES, "revision_plot")


# --- functions
def revision_plot(data: DataT, **kwargs) -> Axes:
    """
    Plot the revisions to ABS data.

    Arguments
    data: pd.DataFrame - the data to plot, the DataFrame has a
        column for each data revision
    recent: int - the number of recent data points to plot
    kwargs : dict :
        -   units: str - the units for the data (Note: you may need to
            recalibrate the units for the y-axis)
        -   rounding: int | bool - if True apply default rounding, otherwise
            apply int rounding.
    """

    # --- check the kwargs and data
    me = "revision_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(REVISION_KW_TYPES, me, **kwargs)

    data = check_clean_timeseries(data, me)

    # --- critical defaults
    kwargs["plot_from"] = kwargs.get("plot_from", -19)

    # --- plot
    axes = line_plot(data, **kwargs)

    # --- Annotate the last value in each series ...
    rounding: int | bool = kwargs.pop(ROUNDING, True)
    for c in data.columns:
        col: Series = data.loc[:, c].dropna()
        annotate_series(col, axes, color="#222222", rounding=rounding, fontsize="small")

    return axes
