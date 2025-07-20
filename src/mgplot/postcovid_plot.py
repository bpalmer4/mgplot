"""Plot the pre-COVID trajectory against the current trend."""

from typing import NotRequired, Unpack, cast

from matplotlib.axes import Axes
from numpy import array, polyfit
from pandas import DataFrame, Period, PeriodIndex, Series, period_range

from mgplot.keyword_checking import (
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT, get_setting
from mgplot.utilities import check_clean_timeseries

# --- constants
ME = "postcovid_plot"
MIN_REGRESSION_POINTS = 10  # minimum number of points before making a regression

# Default regression periods by frequency
DEFAULT_PERIODS = {
    "Q": {"start": "2014Q4", "end": "2019Q4"},
    "M": {"start": "2015-01", "end": "2020-01"},
    "D": {"start": "2015-01-01", "end": "2020-01-01"},
}


class PostcovidKwargs(LineKwargs):
    """Keyword arguments for the post-COVID plot."""

    start_r: NotRequired[Period]  # start of regression period
    end_r: NotRequired[Period]  # end of regression period


# --- functions
def get_projection(original: Series, to_period: Period) -> Series:
    """Create a linear projection based on pre-COVID data.

    Assumes the start of the data has been trimmed to the period before COVID.

    Args:
        original: Series - the original series with a PeriodIndex
            Assume the index is a PeriodIndex, that is unique and monotonic increasing.
        to_period: Period - the period to which the projection should extend.

    Returns:
        Series: A pandas Series with linear projection values using the same index as original.

    Raises:
        ValueError: If to_period is not within the original series index range.

    """
    # --- using ordinals to manage gaps during the regression period (eg in Job Vacancy data)
    op_index = cast("PeriodIndex", original.index)
    y_regress = original[original.index <= to_period].to_numpy()
    x_regress = array([p.ordinal for p in op_index if p <= to_period])
    x_complete = array([p.ordinal for p in op_index])
    m, b = polyfit(x_regress, y_regress, 1)
    regression = Series((x_complete * m) + b, index=original.index)
    regression = regression.reindex(period_range(start=op_index[0], end=op_index[-1])).interpolate(
        method="linear"
    )
    regression.index.name = original.index.name
    return regression


def regression_period(data: Series, **kwargs: Unpack[PostcovidKwargs]) -> tuple[Period, Period, bool]:
    """Establish the regression period.

    Args:
        data: Series - the original time series data.
        **kwargs: Additional keyword arguments.

    Returns:
        A tuple containing the start and end periods for regression,
        and a boolean indicating if the period is robust.

    """
    # --- check that the series index is a PeriodIndex with a valid frequency
    series_index = PeriodIndex(data.index)
    freq_str = series_index.freqstr
    freq_key = freq_str[0]
    if not freq_str or freq_key not in ("Q", "M", "D"):
        raise ValueError("The series index must have a D, M or Q frequency")

    # --- set the default regression period
    default_periods = DEFAULT_PERIODS[freq_key]
    start_regression = Period(default_periods["start"], freq=freq_str)
    end_regression = Period(default_periods["end"], freq=freq_str)

    # --- Override defaults with user-provided periods if specified
    user_start = kwargs.pop("start_r", None)
    user_end = kwargs.pop("end_r", None)

    start_r = Period(user_start, freq=freq_str) if user_start else start_regression
    end_r = Period(user_end, freq=freq_str) if user_end else end_regression

    # --- Validate the regression period
    robust = True
    if start_r >= end_r:
        print(f"Invalid regression period: {start_r=}, {end_r=}")
        robust = False
    no_nan_series = data.dropna()
    if (
        number := len(no_nan_series[(no_nan_series.index >= start_r) & (no_nan_series.index <= end_r)])
    ) < MIN_REGRESSION_POINTS:
        print(f"Insufficient data points (n={number}) for regression.")
        robust = False

    return start_r, end_r, robust


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

    # rely on line_plot() to validate kwargs, but remove any that are not relevant
    if "plot_from" in kwargs:
        print("Warning: the 'plot_from' argument is ignored in postcovid_plot().")
        del kwargs["plot_from"]

    # --- set the regression period
    start_r, end_r, robust = regression_period(data, **kwargs)
    kwargs.pop("start_r", None)  # remove from kwargs to avoid confusion
    kwargs.pop("end_r", None)  # remove from kwargs to avoid confusion
    if not robust:
        print("No valid regression period found; plotting raw data only.")
        return line_plot(
            data,
            **cast("LineKwargs", kwargs),
        )

    # --- combine data and projection
    if start_r < data.dropna().index.min():
        print(f"Caution: Regression start period pre-dates the series index: {start_r=}")
    recent_data = data[data.index >= start_r].copy()
    recent_data.name = "Series"
    projection_data = get_projection(recent_data, end_r)
    projection_data.name = "Pre-COVID projection"

    # --- Create DataFrame with proper column alignment
    combined_data = DataFrame(
        {
            projection_data.name: projection_data,
            recent_data.name: recent_data,
        }
    )

    # --- activate plot settings
    kwargs["width"] = kwargs.pop(
        "width",
        (get_setting("line_normal"), get_setting("line_wide")),
    )  # series line is thicker than projection
    kwargs["style"] = kwargs.pop("style", ("--", "-"))  # dashed regression line
    kwargs["label_series"] = kwargs.pop("label_series", True)
    kwargs["annotate"] = kwargs.pop("annotate", (False, True))  # annotate series only
    kwargs["color"] = kwargs.pop("color", ("darkblue", "#dd0000"))
    kwargs["dropna"] = kwargs.pop("dropna", False)  # drop NaN values

    return line_plot(
        combined_data,
        **cast("LineKwargs", kwargs),
    )
