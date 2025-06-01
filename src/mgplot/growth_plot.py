"""
growth_plot.py:
plot period and annual/through-the-year growth rates on the same axes.
- calc_growth()
- raw_growth_plot()
- series_growth_plot()
"""

# --- imports
from typing import Final
from pandas import Series, DataFrame, Index, Period, PeriodIndex, period_range
from numpy import nan
from matplotlib.pyplot import Axes
import matplotlib.patheffects as pe
from tabulate import tabulate

from mgplot.finalise_plot import make_legend
from mgplot.test import prepare_for_test
from mgplot.settings import get_setting, DataT
from mgplot.date_utils import set_labels
from mgplot.utilities import annotate_series, check_clean_timeseries, default_rounding
from mgplot.kw_type_checking import (
    validate_kwargs,
    report_kwargs,
    validate_expected,
    ExpectedTypeDict,
)


# --- constants
ANNUAL = "annual"
PERIODIC = "periodic"

ANNOTATE_BAR = "annotate_bar"
ANNOTATE_LINE = "annotate_line"
BAR_ROUNDING = "bar_rounding"
ROUNDING = "rounding"


RAW_GROWTH_KW_TYPES: Final[ExpectedTypeDict] = {
    "line_width": (float, int),
    "line_color": str,
    "line_style": str,
    ANNOTATE_LINE: (type(None), bool, int, str),  # None, True or fontsize
    ROUNDING: (type(None), bool, int),  # None, True or rounding
    "bar_width": float,
    "bar_color": str,
    ANNOTATE_BAR: (type(None), bool, int, str),  # None, True or fontsize
    BAR_ROUNDING: (type(None), bool, int),  # None, True or rounding
    "plot_from": (type(None), Period, int),
    "max_ticks": int,
    "legend": (type(None), bool, dict, (str, object)),
}
validate_expected(RAW_GROWTH_KW_TYPES, "growth_plot")
SERIES_GROWTH_KW_TYPES: Final[ExpectedTypeDict] = {
    "ylabel": (str, type(None)),
} | RAW_GROWTH_KW_TYPES
validate_expected(SERIES_GROWTH_KW_TYPES, "growth_plot")


# --- functions
def calc_growth(series: Series) -> DataFrame:
    """
    Calculate annual and periodic growth for a pandas Series,
    where the index is a PeriodIndex.

    Args:
    -   series: A pandas Series with an appropriate PeriodIndex.

    Returns a two column DataFrame:

    Raises
    -   TypeError if the series is not a pandas Series.
    -   TypeError if the series index is not a PeriodIndex.
    -   ValueError if the series is empty.
    -   ValueError if the series index does not have a frequency of Q, M, or D.
    -   ValueError if the series index has duplicates.
    """

    # --- sanity checks
    if not isinstance(series, Series):
        raise TypeError("The series argument must be a pandas Series")
    if not isinstance(series.index, PeriodIndex):
        raise TypeError("The series index must be a pandas PeriodIndex")
    if series.empty:
        raise ValueError("The series argument must not be empty")
    if series.index.freqstr[0] not in ("Q", "M", "D"):
        raise ValueError("The series index must have a frequency of Q, M, or D")
    if series.index.has_duplicates:
        raise ValueError("The series index must not have duplicate values")

    # --- ensure the index is complete and the date is sorted
    complete = period_range(start=series.index.min(), end=series.index.max())
    series = series.reindex(complete, fill_value=nan)
    series = series.sort_index(ascending=True)

    # --- calculate annual and periodic growth
    ppy = {"Q": 4, "M": 12, "D": 365}[PeriodIndex(series.index).freqstr[:1]]
    annual = series.pct_change(periods=ppy) * 100
    periodic = series.pct_change(periods=1) * 100
    periodic_name = {4: "Quarterly", 12: "Monthly", 365: "Daily"}[ppy] + " Growth"
    return DataFrame(
        {
            "Annual Growth": annual,
            periodic_name: periodic,
        }
    )


def _annotations(
    annual: Series,
    periodic: Series,
    axes: Axes,
    **kwargs,
) -> None:
    """Apply annotations the annual and periodic growth series."""

    # --- annotate the end of the line
    annotate_line = kwargs.get(ANNOTATE_LINE, True)  #
    if annotate_line is not None and annotate_line is not False:
        fontsize = kwargs.pop("fontsize", annotate_line)
        annotate_series(annual, axes, fontsize=fontsize, **kwargs)

    # --- annotate each bar
    annotate_bar = kwargs.get(ANNOTATE_BAR, True)  # really fontsize
    if annotate_bar is None or annotate_bar is False:
        return
    if annotate_bar is True:
        annotate_bar = "small"
    max_annotations = 25
    if len(periodic) > max_annotations:
        return

    rounding = kwargs.get(BAR_ROUNDING, True)
    if rounding is None or isinstance(rounding, bool):
        value = periodic.abs().max()
        rounding = default_rounding(value)
    annotate_style = {
        "fontsize": annotate_bar,
        "fontname": "Helvetica",
    }
    adjustment = (periodic.max() - periodic.min()) * 0.01
    for i, value in enumerate(periodic):
        va = "bottom" if value >= 0 else "top"
        text = axes.text(
            periodic.index[i],
            adjustment if value >= 0 else -adjustment,
            f"{value:.{rounding}f}",
            ha="center",
            va=va,
            **annotate_style,
            color="white",
        )
        text.set_path_effects(
            [pe.withStroke(linewidth=2, foreground=kwargs.get("bar_color", "#dd0000"))]
        )


def raw_growth_plot(
    data: DataT,
    **kwargs,
) -> Axes:
    """
    Plot annual (as a line) and periodic (as bars) growth on the
    same axes.

    Args:
    -   data: A pandas DataFrame with two columns:
    -   kwargs:
        -   line_width: The width of the line (default is 2).
        -   line_color: The color of the line (default is "darkblue").
        -   line_style: The style of the line (default is "-").
        -   annotate_line: None | bool | int | str - fontsize to annotate
            the line (default is "small", which means the line is annotated with
            small text).
        -   rounding: None | bool | int - the number of decimal places to round
            the line (default is 0).
        -   bar_width: The width of the bars (default is 0.8).
        -   bar_color: The color of the bars (default is "indianred").
        -   annotate_bar: None | int | str - fontsize to annotate the bars
            (default is "small", which means the bars are annotated with
            small text).
        -   bar_rounding: The number of decimal places to round the
            annotations to (default is 1).
        -   plot_from: None | Period | int -- if:
            -   None: the entire series is plotted
            -   Period: the plot starts from this period
            -   int: the plot starts from this +/- index position
        -   max_ticks: The maximum number of ticks to show on the x-axis
            (default is 10).

    Returns:
    -   axes: The matplotlib Axes object.

    Raises:
    -   TypeError if the annual and periodic arguments are not pandas Series.
    -   TypeError if the annual index is not a PeriodIndex.
    -   ValueError if the annual and periodic series do not have the same index.
    """

    # --- check the kwargs
    me = "raw_growth_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(RAW_GROWTH_KW_TYPES, me, **kwargs)

    # --- data checks
    data = check_clean_timeseries(data, me)
    if len(data.columns) != 2:
        raise TypeError("The data argument must be a pandas DataFrame with two columns")

    # --- get the series of interest ...
    annual = data[data.columns[0]]
    periodic = data[data.columns[1]]

    # --- plot
    plot_from: None | Period | int = kwargs.get("plot_from", None)
    if plot_from is not None:
        if isinstance(plot_from, int):
            plot_from = annual.index[plot_from]
        annual = annual[annual.index >= plot_from]
        periodic = periodic[periodic.index >= plot_from]

    save_index = PeriodIndex(annual.index).copy()
    annual.index = Index(range(len(annual)))
    annual.name = "Annual Growth"
    periodic.index = annual.index
    periodic.name = {"M": "Monthly", "Q": "Quarterly", "D": "Daily"}[
        PeriodIndex(save_index).freqstr[:1]
    ] + " Growth"
    color = kwargs.get("bar_color", "#dd0000")
    kwargs["bar_color"] = color  # for annotations
    axes = periodic.plot.bar(
        color=color,
        width=kwargs.get("bar_width}", 0.8),
    )
    thin_threshold = 180
    annual.plot(
        ax=axes,
        color=kwargs.get("line_color", "darkblue"),
        lw=kwargs.get(
            "line_width",
            (
                get_setting("line_normal")
                if len(annual) >= thin_threshold
                else get_setting("line_wide")
            ),
        ),
        linestyle=kwargs.get("line_style", "-"),
    )
    _annotations(annual, periodic, axes, **kwargs)

    # --- expose the legend by default
    legend = kwargs.get("legend", True)
    make_legend(axes, legend)

    # --- fix the x-axis labels
    set_labels(axes, save_index, kwargs.get("max_ticks", 10))

    # --- and done ...
    return axes


def series_growth_plot(
    data: DataT,
    **kwargs,
) -> Axes:
    """
    Plot annual and periodic growth from a pandas Series,
    and finalise the plot.

    Args:
    -   data: A pandas Series with an appropriate PeriodIndex.
    -   kwargs:
        -   takes the same kwargs as for growth_plot()
    """

    # --- check the kwargs
    me = "series_growth_plot"
    report_kwargs(called_from=me, **kwargs)
    validate_kwargs(SERIES_GROWTH_KW_TYPES, me, **kwargs)

    # --- sanity checks
    if not isinstance(data, Series):
        raise TypeError(
            "The data argument to series_growth_plot() must be a pandas Series"
        )

    # --- calculate growth and plot - add ylabel
    ylabel: str | None = kwargs.pop("ylabel", None)
    if ylabel is not None:
        print(f"Did you intend to specify a value for the 'ylabel' in {me}()?")
    ylabel = "Growth (%)" if ylabel is None else ylabel
    growth = calc_growth(data)
    ax = raw_growth_plot(growth, **kwargs)
    ax.set_ylabel(ylabel)
    return ax


# --- test code
if __name__ == "__main__":
    print("Testing")
    prepare_for_test("growth_plot")
    series_ = Series([1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0])
    series_.index = period_range("2020Q1", periods=len(series_), freq="Q")
    growth_ = calc_growth(series_)
    text_ = tabulate(growth_, headers="keys", tablefmt="pipe")  # type: ignore[arg-type]
    print(text_)
