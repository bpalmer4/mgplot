"""
seas_trend_plot.py
This module contains a function to create seasonal+trend plots.
"""

# --- imports
from matplotlib.pyplot import Axes

from mgplot.settings import DataT
from mgplot.line_plot import line_plot, LINE_KW_TYPES
from mgplot.utilities import get_color_list, get_setting, check_clean_timeseries
from mgplot.kw_type_checking import report_kwargs, validate_kwargs


# --- constants
SEASTREND_KW_TYPES = LINE_KW_TYPES

COLOR = "color"
WIDTH = "width"
STYLE = "style"
ANNOTATE = "annotate"
ROUNDING = "rounding"
LEGEND = "legend"
DROPNA = "dropna"


# --- public functions
def seastrend_plot(data: DataT, **kwargs) -> Axes:
    """
    Publish a DataFrame, where the first column is seasonally
    adjusted data, and the second column is trend data.

    Aguments:
    - data: DataFrame - the data to plot with the first column
      being the seasonally adjusted data, and the second column
      being the trend data.
    The remaining arguments are the same as those passed to
    line_plot().

    Returns:
    - a matplotlib Axes object
    """

    # Note: we will rely on the line_plot() function to do most of the work.
    # including constraining the data to the plot_from keyword argument.

    # --- check the kwargs
    me = "seastrend_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(SEASTREND_KW_TYPES, me, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, me)
    if len(data.columns) < 2:
        raise ValueError(
            "seas_trend_plot() expects a DataFrame data item with at least 2 columns."
        )

    # --- defaults if not in kwargs
    colors = kwargs.pop(COLOR, get_color_list(2))
    widths = kwargs.pop(WIDTH, [get_setting("line_normal"), get_setting("line_wide")])
    styles = kwargs.pop(STYLE, ["-", "-"])
    annotations = kwargs.pop(ANNOTATE, [True, False])
    rounding = kwargs.pop(ROUNDING, True)
    legend = kwargs.pop(LEGEND, True)

    # series breaks are common in seas-trend data
    kwargs[DROPNA] = kwargs.pop(DROPNA, False)

    return line_plot(
        data,
        color=colors,
        width=widths,
        style=styles,
        annotate=annotations,
        rounding=rounding,
        legend=legend,
        **kwargs,
    )
