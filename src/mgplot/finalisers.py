# mypy: disable-error-code="misc"
"""
finalisers.py

Simple convenience functions to finalise and produce plots.
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

# --- imports
from typing import Unpack
from pandas import DataFrame, Period, PeriodIndex

from mgplot.settings import DataT
from mgplot.keyword_checking import validate_kwargs
from mgplot.finalise_plot import FinaliseKwargs
from mgplot.multi_plot import plot_then_finalise
from mgplot.line_plot import line_plot, LineKwargs
from mgplot.bar_plot import bar_plot, BarKwargs
from mgplot.seastrend_plot import seastrend_plot
from mgplot.postcovid_plot import postcovid_plot, PostcovidKwargs
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import run_plot, RunKwargs
from mgplot.growth_plot import (
    series_growth_plot,
    growth_plot,
    GrowthKwargs,
    SeriesGrowthKwargs,
)
from mgplot.summary_plot import summary_plot, SummaryKwargs
from mgplot.utilities import label_period


def impose_legend(
    kwargs,
    data: DataT | None = None,
    force: bool = False,
) -> None:
    """
    A convenience function to call legend() if warranted.
    """
    if force or (isinstance(data, DataFrame) and len(data.columns) > 1):
        kwargs["legend"] = kwargs.get("legend", True)


# --- public functions
class LPFKwargs(LineKwargs, FinaliseKwargs):
    """combined kwargs for line_plot_finalise()"""


def line_plot_finalise(
    data: DataT,
    **kwargs: Unpack[LPFKwargs],
) -> None:
    """
    A convenience function to call line_plot() then finalise_plot().
    """
    validate_kwargs(schema=LPFKwargs, caller="line_plot_finalise", **kwargs)
    impose_legend(data=data, kwargs=kwargs)
    plot_then_finalise(data, function=line_plot, **kwargs)


class BPFKwargs(BarKwargs, FinaliseKwargs):
    """combined kwargs for bar_plot_finalise()"""


def bar_plot_finalise(
    data: DataT,
    **kwargs: Unpack[BPFKwargs],
) -> None:
    """
    A convenience function to call bar_plot() and finalise_plot().
    """
    validate_kwargs(schema=BPFKwargs, caller="bar_plot_finalise", **kwargs)
    impose_legend(data=data, kwargs=kwargs)
    plot_then_finalise(
        data,
        function=bar_plot,
        **kwargs,
    )


class SFKwargs(LineKwargs, FinaliseKwargs):
    """combined kwargs for seastrend_plot_finalise()"""


def seastrend_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SFKwargs],
) -> None:
    """
    A convenience function to call seas_trend_plot() and finalise_plot().
    """
    validate_kwargs(schema=SFKwargs, caller="seastrend_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data, function=seastrend_plot, **kwargs)


class PCFKwargs(PostcovidKwargs, FinaliseKwargs):
    """combined kwargs for postcovid_plot_finalise()"""


def postcovid_plot_finalise(
    data: DataT,
    **kwargs: Unpack[PCFKwargs],
) -> None:
    """
    A convenience function to call postcovid_plot() and finalise_plot().
    """
    validate_kwargs(schema=PCFKwargs, caller="postcovid_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data, function=postcovid_plot, **kwargs)


class RevPFKwargs(LineKwargs, FinaliseKwargs):
    """combined kwargs for revision_plot_finalise()"""


def revision_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RevPFKwargs],
) -> None:
    """
    A convenience function to call revision_plot() and finalise_plot().
    """
    validate_kwargs(schema=RevPFKwargs, caller="revision_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=revision_plot, **kwargs)


class RunPFKwargs(RunKwargs, FinaliseKwargs):
    """combined kwargs for run_plot_finalise()"""


def run_plot_finalise(
    data: DataT,
    **kwargs: Unpack[RunPFKwargs],
) -> None:
    """
    A convenience function to call run_plot() and finalise_plot().
    """
    validate_kwargs(schema=RunPFKwargs, caller="run_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=run_plot, **kwargs)


class SGFPKwargs(SeriesGrowthKwargs, FinaliseKwargs):
    """combined kwargs for series_growth_plot_finalise()"""


def series_growth_plot_finalise(data: DataT, **kwargs: Unpack[SGFPKwargs]) -> None:
    """
    A convenience function to call series_growth_plot() and finalise_plot().
    """
    validate_kwargs(schema=SGFPKwargs, caller="series_growth_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=series_growth_plot, **kwargs)


class GrowthPFKwargs(GrowthKwargs, FinaliseKwargs):
    """combined kwargs for growth_plot_finalise()"""


def growth_plot_finalise(data: DataT, **kwargs: Unpack[GrowthPFKwargs]) -> None:
    """
    A convenience function to call series_growth_plot() and finalise_plot().
    Use this when you are providing the raw growth data. Don't forget to
    set the ylabel in kwargs.
    """
    validate_kwargs(schema=GrowthPFKwargs, caller="growth_plot_finalise", **kwargs)
    impose_legend(force=True, kwargs=kwargs)
    plot_then_finalise(data=data, function=growth_plot, **kwargs)


class SumPFKwargs(SummaryKwargs, FinaliseKwargs):
    """combined kwargs for summary_plot_finalise()"""


def summary_plot_finalise(
    data: DataT,
    **kwargs: Unpack[SumPFKwargs],
) -> None:
    """
    A convenience function to call summary_plot() and finalise_plot().
    This is more complex than most of the above convienience methods.

    Arguments
    - data: DataFrame containing the summary data. The index must be a PeriodIndex.
    - kwargs: additional arguments for the plot
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
