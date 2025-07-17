"""Plot the pre-COVID trajectory against the current trend."""

from typing import NotRequired, Unpack, cast

from matplotlib.axes import Axes
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
        original: Series - the original series with a PeriodIndex.
        to_period: Period - the period to which the projection should extend.

    Returns:
        Series: A pandas Series with linear projection values using the same index as original.

    Raises:
        ValueError: If to_period is not within the original series index range.

    """
    if to_period not in original.index:
        raise ValueError(f"Regression end period {to_period} not found in series index")
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

    series_index = PeriodIndex(data.index)
    freq_str = series_index.freqstr
    if not freq_str or freq_str[0] not in ("Q", "M", "D"):
        raise ValueError("The series index must have a D, M or Q frequency")

    freq_key = freq_str[0]

    # rely on line_plot() to validate kwargs
    if "plot_from" in kwargs:
        print("Warning: the 'plot_from' argument is ignored in postcovid_plot().")
        del kwargs["plot_from"]

    # --- plot COVID counterfactual
    default_periods = DEFAULT_PERIODS[freq_key]
    start_regression = Period(default_periods["start"], freq=freq_str)
    end_regression = Period(default_periods["end"], freq=freq_str)

    # Override defaults with user-provided periods if specified
    user_start = kwargs.pop("start_r", None)
    user_end = kwargs.pop("end_r", None)

    if user_start is not None:
        start_regression = Period(user_start, freq=freq_str)
    if user_end is not None:
        end_regression = Period(user_end, freq=freq_str)

    # Validate regression period
    if start_regression >= end_regression:
        raise ValueError("Start period must be before end period")

    if start_regression not in data.index:
        raise ValueError(f"Regression start period {start_regression} not found in series")
    if end_regression not in data.index:
        raise ValueError(f"Regression end period {end_regression} not found in series")

    # --- combine data and projection
    recent_data = data[data.index >= start_regression].copy()
    recent_data.name = "Series"
    projection_data = get_projection(recent_data, end_regression)
    projection_data.name = "Pre-COVID projection"

    # Create DataFrame with proper column alignment
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

    return line_plot(
        combined_data,
        **cast("LineKwargs", kwargs),
    )
