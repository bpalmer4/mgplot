"""
growth_plot.py:
plot period and annual/through-the-year growth rates on the same axes.
"""

# --- imports
from pandas import Series, Index, Period, PeriodIndex, period_range
from numpy import nan, random
from matplotlib.pyplot import Axes
import matplotlib.patheffects as pe

from mgplot.finalise_plot import finalise_plot, get_finalise_kwargs_list
from mgplot.test import prepare_for_test
from mgplot.settings import get_setting
from mgplot.date_utils import set_labels
from mgplot.utilities import annotate_series


# --- functions
def calc_growth(series: Series) -> tuple[Series, Series]:
    """
    Calculate annual and periodic growth for a pandas Series,
    where the index is a PeriodIndex.

    Args:
    -   series: A pandas Series with an appropriate PeriodIndex.

    Returns a two element tuple:
    -   annual: A pandas Series with the annual growth rate.
    -   periodic: A pandas Series with the periodic growth rate.

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

    # --- ensure the index is complete and date sorted
    complete = period_range(start=series.index.min(), end=series.index.max())
    series = series.reindex(complete, fill_value=nan)
    series = series.sort_index(ascending=True)

    # --- calculate annual and periodic growth
    ppy = {"Q": 4, "M": 12, "D": 365}[PeriodIndex(series.index).freqstr[:1]]
    annual = series.pct_change(periods=ppy) * 100
    periodic = series.pct_change(periods=1) * 100
    return annual, periodic


def _annotations(
    annual: Series,
    periodic: Series,
    axes: Axes,
    **kwargs,
) -> None:
    """Apply annotations the annual and periodic growth series."""

    annotate_line = kwargs.get("annotate_line", "small")
    if annotate_line is not None:
        annotate_series(
            annual,
            axes,
            fontsize=annotate_line,
            color=kwargs.get("line_color", "darkblue"),
        )

    annotate_bar = kwargs.get("annotate_bar", "small")
    max_annotations = 30
    if annotate_bar is not None and len(periodic) < max_annotations:
        annotation_rounding = kwargs.get("annotation_rounding", 1)
        annotate_style = {
            "fontsize": annotate_bar,
            "fontname": "Helvetica",
        }
        adjustment = (periodic.max() - periodic.min()) * 0.005
        for i, value in enumerate(periodic):
            va = "bottom" if value >= 0 else "top"
            text = axes.text(
                periodic.index[i],
                adjustment if value >= 0 else -adjustment,
                f"{value:.{annotation_rounding}f}",
                ha="center",
                va=va,
                **annotate_style,
                fontdict=None,
                color="white",
            )
            text.set_path_effects(
                [
                    pe.withStroke(
                        linewidth=2, foreground=kwargs.get("bar_color", "indianred")
                    )
                ]
            )


def growth_plot(
    annual: Series,
    periodic: Series,
    **kwargs,
) -> Axes:
    """
    Plot annual (as a line) and periodic (as bars) growth on the
    same axes.

    Args:
    -   annual: A pandas Series with the annual growth rate.
    -   periodic: A pandas Series with the periodic growth rate.
    -   kwargs:
        -   line_width: The width of the line (default is 2).
        -   line_color: The color of the line (default is "darkblue").
        -   line_style: The style of the line (default is "-").
        -   annotate_line: None | int | str - fontsize to annotate the line
            (default is "small", which means the line is annotated with
            small text).
        -   bar_width: The width of the bars (default is 0.8).
        -   bar_color: The color of the bars (default is "indianred").
        -   annotate_bar: None | int | str - fontsize to annotate the bars
            (default is "small", which means the bars are annotated with
            small text).
        -   annotation_rounding: The number of decimal places to round the
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

    # --- sanity checks
    if not isinstance(annual, Series):
        raise TypeError("The annual argument must be a pandas Series")
    if not isinstance(periodic, Series):
        raise TypeError("The periodic argument must be a pandas Series")
    if not isinstance(annual.index, PeriodIndex):
        raise TypeError("The annual index must be a pandas PeriodIndex")
    if not annual.index.equals(periodic.index):
        raise ValueError("The annual and periodic series must have the same index")

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
    axes = periodic.plot.bar(
        color=kwargs.get("bar_color", "indianred"),
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
    axes.set_ylabel("Per cent Growth")

    # --- fix the x-axis labels
    set_labels(axes, save_index, kwargs.get("max_ticks", 10))

    # --- and done ...
    axes.legend()
    return axes


def growth_plot_from_series(
    series: Series,
    **kwargs,
) -> None:
    """
    Plot annual and periodic growth from a pandas Series,
    and finalise the plot.

    Args:
    -   series: A pandas Series with an appropriate PeriodIndex.
    -   kwargs:
        -   takes the same kwargs as for growth_plot() and finalise_plot()
    """

    annual, periodic = calc_growth(series)
    ax = growth_plot(annual, periodic, **kwargs)
    fp_kwargs = {k: v for k, v in kwargs.items() if k in get_finalise_kwargs_list()}
    fp_kwargs["ylabel"] = "Per cent Growth"
    if (periodic < 0).any() and (periodic > 0).any():
        # include a y=0 line when positive and negative values are present
        fp_kwargs["y0"] = fp_kwargs.get("y0", True)
    finalise_plot(
        ax,
        **fp_kwargs,
    )


# --- test
if __name__ == "__main__":

    # --- set up
    prepare_for_test("growth_plot")

    # --- run the test
    index = PeriodIndex(period_range("2020-Q1", "2025-Q4", freq="Q"))
    data = Series([0.1] * len(index), index=index).cumsum()
    data += random.normal(1, 0.02, len(index))
    growth_plot_from_series(
        data,
        plot_from=4,
        title="Growth Rates Test",
        rfooter="Fake data",
    )
