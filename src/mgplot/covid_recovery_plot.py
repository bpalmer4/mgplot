"""
covid_recovery_plot.py
Plot the pre-COVID trajectory against the current trend.
"""

# --- imports
from pandas import DataFrame, Series, Period, PeriodIndex
from numpy import arange, polyfit

from mgplot.finalise_plot import line_plot_finalise
from mgplot.settings import get_setting


# --- constants
DROPNA = "dropna"
LEGEND = "legend"
LFOOTER = "lfooter"


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


def covid_recovery_plot(series: Series, **kwargs) -> None:
    """
    Plots a series with a PeriodIndex.

    Arguments
    - series to be plotted
    - **kwargs - same as for finalise_plot().

    Raises:
    - TypeError if series is not a pandas Series
    - TypeError if series does not have a PeriodIndex
    - ValueError if series does not have a D, M or Q frequency
    - ValueError if regression start is after regression end
    """

    # sanity checks
    if not isinstance(series, Series):
        raise TypeError("The series argument must be a pandas Series")
    if not isinstance(series.index, PeriodIndex):
        raise TypeError("The series must have a pandas PeriodIndex")
    if series.index.freqstr[:1] not in ("Q", "M", "D"):
        raise ValueError("The series index must have a D, M or Q freq")

    # plot COVID counterfactural
    freq = series.index.freqstr
    match freq[0]:
        case "Q":
            start_regression = Period("2014Q4", freq=freq)
            end_regression = Period("2019Q4", freq=freq)
        case "M":
            start_regression = Period("2015-01-31", freq=freq)
            end_regression = Period("2020-01-31", freq=freq)
        case "D":
            start_regression = Period("2015-01-01", freq=freq)
            end_regression = Period("2020-01-01", freq=freq)

    start_regression = Period(kwargs.pop("start_r", start_regression), freq=freq)
    end_regression = Period(kwargs.pop("end_r", end_regression), freq=freq)
    if start_regression >= end_regression:
        raise ValueError("Start period must be before end period")

    recent = series[series.index >= start_regression].copy()
    recent.name = "Series"
    projection = get_projection(recent, end_regression)
    projection.name = "Pre-COVID projection"
    data_set = DataFrame([projection, recent]).T
    kwargs[LFOOTER] = (
        kwargs.get(LFOOTER, "")
        + f"Projection from {start_regression} to {end_regression}. "
    )

    kwargs[DROPNA] = kwargs.get(DROPNA, False)
    kwargs[LEGEND] = kwargs.get(LEGEND, get_setting("legend"))

    line_plot_finalise(
        data_set,
        width=[get_setting("line_normal"), get_setting("line_wide")],
        style=["--", "-"],
        **kwargs,
    )
