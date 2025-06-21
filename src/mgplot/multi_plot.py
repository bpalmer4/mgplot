"""Chain together multiple plotting actions.

Key functions:
- plot_then_finalise()
- multi_start()
- multi_column()

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

from collections.abc import Callable, Iterable
from typing import Any, Final, cast

from pandas import DataFrame, Period

from mgplot.bar_plot import BarKwargs, bar_plot
from mgplot.finalise_plot import FinaliseKwargs, finalise_plot
from mgplot.growth_plot import (
    GrowthKwargs,
    SeriesGrowthKwargs,
    growth_plot,
    series_growth_plot,
)
from mgplot.keyword_checking import (
    BaseKwargs,
    limit_kwargs,
    report_kwargs,
    validate_kwargs,
)
from mgplot.line_plot import LineKwargs, line_plot
from mgplot.postcovid_plot import PostcovidKwargs, postcovid_plot
from mgplot.revision_plot import revision_plot
from mgplot.run_plot import RunKwargs, run_plot
from mgplot.seastrend_plot import seastrend_plot
from mgplot.settings import DataT
from mgplot.summary_plot import SummaryKwargs, summary_plot

# --- constants
EXPECTED_CALLABLES: dict[Callable, type[Any]] = {
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
    """Extract the first Callable from a function list.

    Args:
        function: Callable | list[Callable] - a Callable or a non-empty list of Callables

    Returns a tuple containing:
        first: Callable - the first function, and
        rest: list[Callable] a list of the remaining functions.

    Raises:
        ValueError if function is an empty list.
        TypeError if function not a Callable or a non-empty list of Callables.

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
        raise TypeError(error_msg)

    return first, rest


# --- public functions
def plot_then_finalise(
    data: DataT,
    function: Callable | list[Callable],
    **kwargs,
) -> None:
    """Chain a plotting function with the finalise_plot() function.

    Args:
        data: Series | DataFrame - The data to be plotted.
        function: Callable | list[Callable] - the desired plotting function(s).
        kwargs: Any - Additional keyword arguments.

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
            "Call them before calling {me}. ",
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
        dict(cast("dict[str, Any]", expected.__annotations__))
        | dict(cast("dict[str, Any]", FinaliseKwargs.__annotations__))
    )
    validate_kwargs(schema=kw_types, caller=me, **kwargs)

    # --- call the first function with the data and selected plot kwargs
    axes = first(data, **plot_kwargs)

    # --- remove potentially overlapping kwargs
    fp_kwargs = limit_kwargs(FinaliseKwargs, **kwargs)
    # To do: remove any duplicate argument passes

    # --- finalise the plot
    finalise_plot(axes, **fp_kwargs)


def multi_start(
    data: DataT,
    function: Callable | list[Callable],
    starts: Iterable[None | Period | int],
    **kwargs,
) -> None:
    """Create multiple plots with different starting points.

    Args:
        data: Series | DataFrame - The data to be plotted.
        function: Callable | list[Callable] - desierd plotting function(s).
        starts: Iterable[Period | int | None] - The starting points.
        kwargs: Any - the other arguments.

    Returns None.

    Raises:
        TypeError if the starts is not an iterable of None, Period or int.

    Note: kwargs['tag'] is used to create a unique tag for each plot.

    """
    # --- sanity checks
    me = "multi_start"
    report_kwargs(caller=me, **kwargs)
    if not isinstance(starts, Iterable):
        raise TypeError("starts must be an iterable of None, Period or int")
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
    """Create multiple plots, one for each column in a DataFrame.

    Note: The plot title will be kwargs["title"] plus the column name.

    Args:
        data: DataFrame - The data to be plotted
        function: Callable - The plotting function to be used.
        kwargs: Any - Additional keyword arguments.

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
