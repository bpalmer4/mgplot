"""Plot the pre-COVID trajectory against the current trend."""

from typing import NotRequired, Unpack, cast

from matplotlib.pyplot import Axes
from numpy import arange, polyfit
from pandas import DataFrame, Period, PeriodIndex, Series

from mgplot.keyword_checking import (
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import check_clean_timeseries

# --- constants
ME = "postcovid_plot"


class PostcovidKwargs(LineKwargs):
    """Keyword arguments for the post-COVID plot."""

    start_r: NotRequired[Period]  # start of regression period
    end_r: NotRequired[Period]  # end of regression period


# --- functions
def get_projection(original: Series, to_period: Period) -> Series:
    """Projection based on the pre-COVID data.

    Assumes the start of the data has been trimmed to the period before COVID.

    Args:
        original: Series - the original series with a PeriodIndex.
        to_period: Period - the period to which the projection should extend.

    Returns a pandas Series with a linear projection.

    """
    y_regress = original[original.index <= to_period].copy()
    x_regress = arange(len(y_regress))
    m, b = polyfit(x_regress, y_regress, 1)

    x_complete = arange(len(original))
    return Series((x_complete * m) + b, index=original.index)


def postcovid_plot(data: DataT, **kwargs: Unpack[PostcovidKwargs]) -> Axes:
    """Plot a series with a PeriodIndex, including a post-COVID projection.

    Args:
        data: Series - the series to be plotted.
        kwargs: PostcovidKwargs - plotting arguments.

    Raises:
        TypeError if series is not a pandas Series
        TypeError if series does not have a PeriodIndex
        ValueError if series does not have a D, M or Q frequency
        ValueError if regression start is after regression end

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=PostcovidKwargs, caller=ME, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, ME)
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

    # --- activate plot settings
    kwargs["width"] = kwargs.pop(
        "width",
        (get_setting("line_normal"), get_setting("line_wide")),
    )  # series line is thicker than projection
    kwargs["style"] = kwargs.pop("style", ("--", "-"))  # dashed regression line
    kwargs["label_series"] = kwargs.pop("label_series", True)
    kwargs["annotate"] = kwargs.pop("annotate", (False, True))  # annotate series only
    kwargs["color"] = kwargs.pop("color", ("darkblue", "#dd0000"))

    return line_plot(
        data_set,
        **cast("LineKwargs", kwargs),
    )
