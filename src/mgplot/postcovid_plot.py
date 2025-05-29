"""
covid_recovery_plot.py
Plot the pre-COVID trajectory against the current trend.
"""

# --- imports
from collections.abc import Sequence
from pandas import DataFrame, Series, Period, PeriodIndex
from matplotlib.pyplot import Axes
from numpy import arange, polyfit

from mgplot.settings import DataT, get_setting
from mgplot.line_plot import line_plot
from mgplot.utilities import check_clean_timeseries
from mgplot.kw_type_checking import report_kwargs, ExpectedTypeDict, validate_expected


# --- constants
WIDTH = "width"
STYLE = "style"
START_R = "start_r"
END_R = "end_r"

POSTCOVID_KW_TYPES: ExpectedTypeDict = {
    WIDTH: (Sequence, (int, float), int, float),
    STYLE: (Sequence, (str,), str),
    START_R: Period,
    END_R: Period,
}
validate_expected(POSTCOVID_KW_TYPES, "postcovid_plot")


# --- functions
def get_projection(original: Series, to_period: Period) -> Series:
    """
    Projection based on data from the start of a series
    to the to_period (inclusive). Returns projection over the whole
    period of the original series.
    """

    y_regress = original[original.index <= to_period].copy()
    x_regress = arange(len(y_regress))
    m, b = polyfit(x_regress, y_regress, 1)

    x_complete = arange(len(original))
    projection = Series((x_complete * m) + b, index=original.index)

    return projection


def postcovid_plot(data: DataT, **kwargs) -> Axes:
    """
    Plots a series with a PeriodIndex.

    Arguments
    - data - the series to be plotted (note that this function
      is designed to work with a single series, not a DataFrame).
    - **kwargs - same as for line_plot() and finalise_plot().

    Raises:
    - TypeError if series is not a pandas Series
    - TypeError if series does not have a PeriodIndex
    - ValueError if series does not have a D, M or Q frequency
    - ValueError if regression start is after regression end
    """

    # --- sanity checks
    report_kwargs(called_from="postcovid_plot", **kwargs)
    data = check_clean_timeseries(data)
    if not isinstance(data, Series):
        raise TypeError("The series argument must be a pandas Series")
    series: Series = data
    series_index = PeriodIndex(series.index)  # syntactic sugar for type hinting
    if series_index.freqstr[:1] not in ("Q", "M", "D"):
        raise ValueError("The series index must have a D, M or Q freq")
    # rely on line_plot() to validate kwargs
    if "plot_from" in kwargs:
        print("Warning: the 'plot_from' argument is ignored in postcovid_plot().")
        del kwargs["plot_from"]

    # --- plot COVID counterfactural
    freq = PeriodIndex(series.index).freqstr  # syntactic sugar for type hinting
    match freq[0]:
        case "Q":
            start_regression = Period("2014Q4", freq=freq)
            end_regression = Period("2019Q4", freq=freq)
        case "M":
            start_regression = Period("2015-01", freq=freq)
            end_regression = Period("2020-01", freq=freq)
        case "D":
            start_regression = Period("2015-01-01", freq=freq)
            end_regression = Period("2020-01-01", freq=freq)

    start_regression = Period(kwargs.pop("start_r", start_regression), freq=freq)
    end_regression = Period(kwargs.pop("end_r", end_regression), freq=freq)
    if start_regression >= end_regression:
        raise ValueError("Start period must be before end period")

    # --- combine data and projection
    recent = series[series.index >= start_regression].copy()
    recent.name = "Series"
    projection = get_projection(recent, end_regression)
    projection.name = "Pre-COVID projection"
    data_set = DataFrame([projection, recent]).T

    kwargs[WIDTH] = kwargs.pop(
        WIDTH, [get_setting("line_normal"), get_setting("line_wide")]
    )
    kwargs[STYLE] = kwargs.pop(STYLE, ["--", "-"])
    kwargs["legend"] = kwargs.pop("legend", True)

    return line_plot(
        data_set,
        **kwargs,
    )
