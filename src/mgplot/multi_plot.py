"""
multi_plot.py

This module provides a function to create multiple plots
from a single dataset
- multi_start()
- multi_column()

And to chain a plotting function with the finalise_plot() function.
- plot_then_finalise()

But there is a downside: Because these functions use dynamic
dispatch, they cannot provide type hints for the
kwargs argument. This means that the user will not get
autocomplete for the keyword arguments of these plotting
functions.

Underlying assumptions:
- every plot function:
    - has a mandatory data: DataFrame | Series argument first (noting
      that some plotting functions only work with Series data, and they
      will raise an error if they are passed a DataFrame).
    - accepts an optional plot_from: int | Period keyword argument
    - returns a matplotlib Axes object
- the multi functions (all in this module)
    - have a mandatory data: DataFrame | Series argument
    - have a mandatory function: Callable | list[Callable] argument
        and otherwise pass their kwargs to the next function
        when execution is transferred to the next function.
    - the multi functions can be chained together.
    - return None.

And why are these three public functions all in the same modules?
- They all work with the same underlying assumptions.
- They all take a function argument/list to which execution is
  passed.
- They all use the same underlying logic to extract the first
  function from the function argument, and to store any remaining
  functions in the kwargs['function'] argument.

Note: rather than pass the kwargs dict directly, we will re-pack-it

"""

# --- imports
from typing import Callable, Final, Any, cast
from collections.abc import Iterable
from pandas import DataFrame, Period

from mgplot.keyword_checking import (
    limit_kwargs,
    report_kwargs,
    validate_kwargs,
    BaseKwargs,
)
from mgplot.finalise_plot import finalise_plot, FinaliseKwargs
from mgplot.settings import DataT

from mgplot.line_plot import line_plot, LineKwargs
from mgplot.bar_plot import bar_plot, BarKwargs
from mgplot.seastrend_plot import seastrend_plot
from mgplot.postcovid_plot import postcovid_plot, PostcovidKwargs
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import run_plot, RunKwargs
from mgplot.summary_plot import summary_plot, SummaryKwargs

from mgplot.growth_plot import (
    series_growth_plot,
    growth_plot,
    GrowthKwargs,
    SeriesGrowthKwargs,
)

# --- constants

EXPECTED_CALLABLES: Final[dict[Callable, type[Any]]] = {
    # used by plot_then_finalise() to (1) check the target function
    # is one of the expected functions, and (2) to limit the kwargs
    # passed on, to the expected keyword arguments for that function.
    line_plot: LineKwargs,
    bar_plot: BarKwargs,
    seastrend_plot: LineKwargs,
    postcovid_plot: PostcovidKwargs,
    revision_plot: LineKwargs,
    run_plot: RunKwargs,
    summary_plot: SummaryKwargs,
    series_growth_plot: SeriesGrowthKwargs,
    growth_plot: GrowthKwargs,
}


# --- private functions
def first_unchain(
    function: Callable | list[Callable],
) -> tuple[Callable, list[Callable]]:
    """
    Extract the first Callable from function (which may be
    a stand alone Callable or a nonr-empty list of Callables).
    Store the remaining Callables in kwargs['function'].
    This allows for chaining multiple functions together.

    Parameters
    - function - a Callable or a non-empty list of Callables

    Returns a tuple containing the first function and a list of the remaining
    functions (which may be empty if there are no remaining functions).

    Raises ValueError if function is an empty list.

    Not intended for direct use by the user.
    """

    error_msg = "function must be a Callable or a non-empty list of Callables"

    if isinstance(function, list):
        if len(function) == 0:
            raise ValueError(error_msg)
        first, *rest = function
    elif callable(function):
        first, rest = function, []
    else:
        raise ValueError(error_msg)

    return first, rest


# --- public functions
def plot_then_finalise(
    data: DataT,
    function: Callable | list[Callable],
    **kwargs,
) -> None:
    """
    Chain a plotting function with the finalise_plot() function.
    This is designed to be the last function in a chain.

    Parameters
    - data: Series | DataFrame - The data to be plotted.
    - function: Callable | list[Callable] - The plotting function
      to be used.
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function, and then the finalise_plot() function.

    Returns None.
    """

    # --- checks
    me = "plot_then_finalise"
    report_kwargs(caller=me, **kwargs)
    # validate once we have established the first function

    # data is not checked here, assume it is checked by the called
    # plot function.

    first, kwargs["function"] = first_unchain(function)
    if not kwargs["function"]:
        del kwargs["function"]  # remove the function key if it is empty

    # --- TO DO: check that the first function is one of the
    bad_next = (multi_start, multi_column)
    if first in bad_next:
        # these functions should not be called by plot_then_finalise()
        raise ValueError(
            f"[{', '.join(k.__name__ for k in bad_next)}] should not be called by {me}. "
            "Call them before calling {me}. "
        )

    if first in EXPECTED_CALLABLES:
        expected = EXPECTED_CALLABLES[first]
        plot_kwargs = limit_kwargs(expected, **kwargs)
    else:
        # this is an unexpected Callable, so we will give it a try
        print(f"Unknown proposed function: {first}; nonetheless, will give it a try.")
        expected = BaseKwargs
        plot_kwargs = kwargs.copy()

    # --- validate the original kwargs (could not do before now)
    kw_types = (
        # combine the expected kwargs types with the finalise kwargs types
        dict(cast(dict[str, Any], expected.__annotations__))
        | dict(cast(dict[str, Any], FinaliseKwargs.__annotations__))
    )
    validate_kwargs(schema=kw_types, caller=me, **kwargs)

    # --- call the first function with the data and selected plot kwargs
    axes = first(data, **plot_kwargs)

    # --- remove potentially overlapping kwargs
    fp_kwargs = limit_kwargs(FinaliseKwargs, **kwargs)
    # overlapping = expected.keys() & FinaliseKwargs.keys()
    # if overlapping:
    #    for key in overlapping:
    #        fp_kwargs.pop(key, None)  # remove overlapping keys from kwargs

    # --- finalise the plot
    finalise_plot(axes, **fp_kwargs)


def multi_start(
    data: DataT,
    function: Callable | list[Callable],
    starts: Iterable[None | Period | int],
    **kwargs,
) -> None:
    """
    Create multiple plots with different starting points.
    Each plot will start from the specified starting point.

    Parameters
    - data: Series | DataFrame - The data to be plotted.
    - function: Callable | list[Callable] - The plotting function
      to be used.
    - starts: Iterable[Period | int | None] - The starting points
      for each plot (None means use the entire data).
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function.

    Returns None.

    Raises
    - ValueError if the starts is not an iterable of None, Period or int.

    Note: kwargs['tag'] is used to create a unique tag for each plot.
    """

    # --- sanity checks
    me = "multi_start"
    report_kwargs(caller=me, **kwargs)
    if not isinstance(starts, Iterable):
        raise ValueError("starts must be an iterable of None, Period or int")
    # data not checked here, assume it is checked by the called
    # plot function.

    # --- check the function argument
    original_tag: Final[str] = kwargs.get("tag", "")
    first, kwargs["function"] = first_unchain(function)
    if not kwargs["function"]:
        del kwargs["function"]  # remove the function key if it is empty

    # --- iterate over the starts
    for i, start in enumerate(starts):
        kw = kwargs.copy()  # copy to avoid modifying the original kwargs
        this_tag = f"{original_tag}_{i}"
        kw["tag"] = this_tag
        kw["plot_from"] = start  # rely on plotting function to constrain the data
        first(data, **kw)


def multi_column(
    data: DataFrame,
    function: Callable | list[Callable],
    **kwargs,
) -> None:
    """
    Create multiple plots, one for each column in a DataFrame.
    The plot title will be the column name.

    Parameters
    - data: DataFrame - The data to be plotted
    - function: Callable - The plotting function to be used.
    - **kwargs: Additional keyword arguments to be passed to
      the plotting function.

    Returns None.
    """

    # --- sanity checks
    me = "multi_column"
    report_kwargs(caller=me, **kwargs)
    if not isinstance(data, DataFrame):
        raise TypeError("data must be a pandas DataFrame for multi_column()")
    # Otherwise, the data is assumed to be checked by the called
    # plot function, so we do not check it here.

    # --- check the function argument
    title_stem = kwargs.get("title", "")
    tag: Final[str] = kwargs.get("tag", "")
    first, kwargs["function"] = first_unchain(function)
    if not kwargs["function"]:
        del kwargs["function"]  # remove the function key if it is empty

    # --- iterate over the columns
    for i, col in enumerate(data.columns):
        series = data[[col]]
        kwargs["title"] = f"{title_stem}{col}" if title_stem else col

        this_tag = f"_{tag}_{i}".replace("__", "_")
        kwargs["tag"] = this_tag

        first(series, **kwargs)
