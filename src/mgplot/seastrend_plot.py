"""Create seasonal+trend plots."""

from typing import Final, Unpack

from matplotlib.pyplot import Axes

from mgplot.keyword_checking import report_kwargs, validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries, get_color_list, get_setting

# --- constants
ME: Final[str] = "seastrend_plot"


# --- public functions
def seastrend_plot(data: DataT, **kwargs: Unpack[LineKwargs]) -> Axes:
    """Produce a seasonal+trend plot.

    Aguments:
        data: DataFrame - the data to plot - Seasonal in column 0, Trend in columm 1
        kwargs: LineKwargs - additional keyword arguments to pass to line_plot()

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
    two_columns: Final[int] = 2
    if data.shape[1] < two_columns:
        raise ValueError(f"{ME}() expects a DataFrame with at least {two_columns} columns.")

    # --- defaults if not in kwargs
    kwargs["color"] = kwargs.get("color", get_color_list(2))
    kwargs["width"] = kwargs.get("width", [get_setting("line_normal"), get_setting("line_wide")])
    kwargs["style"] = kwargs.get("style", ["-", "-"])
    kwargs["annotate"] = kwargs.get("annotate", [True, False])
    kwargs["rounding"] = kwargs.get("rounding", True)

    # series breaks are common in seas-trend data
    kwargs["dropna"] = kwargs.get("dropna", False)

    return line_plot(
        data,
        **kwargs,
    )
