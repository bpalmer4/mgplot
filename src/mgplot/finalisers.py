# mypy: disable-error-code="misc"
"""Simple convenience functions to finalise and produce plots.

Key functions are:
- bar_plot_finalise()
- line_plot_finalise()
- postcovid_plot_finalise()
- growth_plot_finalise()
- revision_plot_finalise()
- run_plot_finalise()
- seastrend_plot_finalise()
- series_growth_plot_finalise()
- summary_plot_finalise()

In the main, these are wrappers around the plot functions
to call plot_then_finalise() with the correct arguments.
Most functions are just a single line of code.

Note: these functions are in a separate module to stop circular imports
"""

from typing import Unpack

from pandas import DataFrame, Period, PeriodIndex

from mgplot.bar_plot import BarKwargs, bar_plot
from mgplot.finalise_plot import FinaliseKwargs
from mgplot.growth_plot import (
    GrowthKwargs,
    SeriesGrowthKwargs,
    growth_plot,
    series_growth_plot,
)
from mgplot.keyword_checking import validate_kwargs
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.multi_plot import plot_then_finalise
from mgplot.postcovid_plot import PostcovidKwargs, postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import RunKwargs, run_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.settings import DataT
from mgplot.summary_plot import SummaryKwargs, summary_plot
from mgplot.utilities import label_period


# --- argument types
class BPFKwargs(BarKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for bar_plot_finalise()."""


class GrowthPFKwargs(GrowthKwargs, FinaliseKwargs):
    """Combined kwargs for growth_plot_finalise()."""


class LPFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs for line_plot_finalise()."""


class PCFKwargs(PostcovidKwargs, FinaliseKwargs):
    """Combined kwargs for postcovid_plot_finalise()."""


class RevPFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for revision_plot_finalise()."""


class RunPFKwargs(RunKwargs, FinaliseKwargs):
    """Combined kwargs for run_plot_finalise()."""


class SFKwargs(LineKwargs, FinaliseKwargs):
    """Combined kwargs TypedDict for seastrend_plot_finalise()."""


class SGFPKwargs(SeriesGrowthKwargs, FinaliseKwargs):
    """Combined kwargs for series_growth_plot_finalise()."""


class SumPFKwargs(SummaryKwargs, FinaliseKwargs):
    """Combined kwargs for summary_plot_finalise()."""


COMBINED_TYPES = (
    LPFKwargs | BPFKwargs | GrowthPFKwargs | PCFKwargs | RevPFKwargs | RunPFKwargs | SFKwargs | SGFPKwargs
)


# --- private functions


def impose_legend(
    kwargs: COMBINED_TYPES,
    data: DataT | None = None,
    *,
    force: bool = False,
) -> None:
    """Ensure legend is set for finalise_plot()."""
    if force or (isinstance(data, DataFrame) and len(data.columns) > 1):
        kwargs["legend"] = kwargs.get("legend", True)


# --- public functions


def bar_plot_finalise(
    data: DataT,
    **kwargs: Unpack[BPFKwargs],
) -> None:
    """Call bar_plot() and finalise_plot()."""
    validate_kwargs(schema=BPFKwargs, caller="bar_plot_finalise", **kwargs)
    impose_legend(data=data, kwargs=kwargs)
    plot_then_finalise(
        data,
        function=bar_plot,
        **kwargs,
    )


def growth_plot_finalise(data: DataT, **kwargs: Unpack[GrowthPFKwargs]) -> None:
    """Call series_growth_plot() and finalise_plot().

    Use this when you are providing the raw growth data. Don't forget to
    set the ylabel in kwargs.
    """
    validate_kwargs(schema=GrowthPFKwargs, caller="growth_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=growth_plot, **kwargs)


def line_plot_finalise(
    data: DataT,
    **kwargs: Unpack[LPFKwargs],
) -> None:
    """Call line_plot() then finalise_plot()."""
    validate_kwargs(schema=LPFKwargs, caller="line_plot_finalise", **kwargs)
    impose_legend(data=data, kwargs=kwargs)
    plot_then_finalise(data, function=line_plot, **kwargs)


def postcovid_plot_finalise(
    data: DataT,
    **kwargs: Unpack[PCFKwargs],
) -> None:
    """Call postcovid_plot() and finalise_plot()."""
    validate_kwargs(schema=PCFKwargs, caller="postcovid_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data, function=postcovid_plot, **kwargs)


def revision_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RevPFKwargs],
) -> None:
    """Call revision_plot() and finalise_plot()."""
    validate_kwargs(schema=RevPFKwargs, caller="revision_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=revision_plot, **kwargs)


def run_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RunPFKwargs],
) -> None:
    """Call run_plot() and finalise_plot()."""
    validate_kwargs(schema=RunPFKwargs, caller="run_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=run_plot, **kwargs)


def seastrend_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SFKwargs],
) -> None:
    """Call seas_trend_plot() and finalise_plot()."""
    validate_kwargs(schema=SFKwargs, caller="seastrend_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data, function=seastrend_plot, **kwargs)


def series_growth_plot_finalise(data: DataT, **kwargs: Unpack[SGFPKwargs]) -> None:
    """Call series_growth_plot() and finalise_plot()."""
    validate_kwargs(schema=SGFPKwargs, caller="series_growth_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=series_growth_plot, **kwargs)


def summary_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SumPFKwargs],
) -> None:
    """Call summary_plot() and finalise_plot().

    This is more complex than most of the above convienience methods.

    Args:
        data: DataFrame containing the summary data. The index must be a PeriodIndex.
        kwargs: additional arguments for the plot

    """
    # --- standard arguments
    if not isinstance(data, DataFrame) and isinstance(data.index, PeriodIndex):
        raise TypeError("Data must be a DataFrame with a PeriodIndex.")
    validate_kwargs(schema=SumPFKwargs, caller="summary_plot_finalise", **kwargs)
    kwargs["title"] = kwargs.get("title", f"Summary at {label_period(data.index[-1])}")
    kwargs["preserve_lims"] = kwargs.get("preserve_lims", True)

    start: int | Period | None = kwargs.get("plot_from", 0)
    if start is None:
        start = data.index[0]
    if isinstance(start, int):
        start = data.index[start]
    kwargs["plot_from"] = start
    if not isinstance(start, Period):
        raise TypeError("plot_from must be a Period or convertible to one")

    pre_tag: str = kwargs.get("pre_tag", "")
    for plot_type in ("zscores", "zscaled"):
        # some sorting of kwargs for plot production
        kwargs["plot_type"] = plot_type
        kwargs["pre_tag"] = pre_tag + plot_type

        plot_then_finalise(
            data,
            function=summary_plot,
            **kwargs,
        )
