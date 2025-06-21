"""Produce a summary plot for the data in a given DataFrame."""

# system imports
from typing import Any, NotRequired, Unpack

from matplotlib.pyplot import Axes

# analytic third-party imports
from numpy import array, ndarray
from pandas import DataFrame, Period

from mgplot.finalise_plot import make_legend
from mgplot.keyword_checking import (
    BaseKwargs,
    report_kwargs,
    validate_kwargs,
)

# local imports
from mgplot.settings import DataT
from mgplot.utilities import check_clean_timeseries, constrain_data, get_axes, label_period

# --- constants
ME = "summary_plot"
ZSCORES = "zscores"
ZSCALED = "zscaled"


class SummaryKwargs(BaseKwargs):
    """Keyword arguments for the summary_plot function."""

    ax: NotRequired[Axes | None]
    verbose: NotRequired[bool]
    middle: NotRequired[float]
    plot_type: NotRequired[str]
    plot_from: NotRequired[int | Period]
    legend: NotRequired[dict[str, Any]]
    xlabel: NotRequired[str | None]


# --- functions
def calc_quantiles(middle: float) -> ndarray:
    """Calculate the quantiles for the middle of the data."""
    return array([(1 - middle) / 2.0, 1 - (1 - middle) / 2.0])


def calculate_z(
    original: DataFrame,
    middle: float,
    *,
    verbose: bool = False,
) -> tuple[DataFrame, DataFrame]:
    """Calculate z-scores, scaled z-scores and middle quantiles.

    Args:
        original: DataFrame containing the original data.
        middle: float, the proportion of data to highlight in the middle (eg. 0.8 for 80%).
        verbose: bool, whether to print the summary data.

    Return z_scores, z_scaled, q (which are the quantiles for the
    start/end of the middle proportion of data to highlight).

    """
    # calculate z-scores, scaled scores and middle quantiles
    z_scores: DataFrame = (original - original.mean()) / original.std()
    z_scaled: DataFrame = (
        # scale z-scores between -1 and +1
        (((z_scores - z_scores.min()) / (z_scores.max() - z_scores.min())) - 0.5) * 2
    )
    q_middle = calc_quantiles(middle)

    if verbose:
        frame = DataFrame(
            {
                "count": original.count(),
                "mean": original.mean(),
                "median": original.median(),
                "min shaded": original.quantile(q=q_middle[0]),
                "max shaded": original.quantile(q=q_middle[1]),
                "z-scores": z_scores.iloc[-1],
                "scaled": z_scaled.iloc[-1],
            },
        )
        print(frame)

    return DataFrame(z_scores), DataFrame(z_scaled)  # syntactic sugar for type hinting


def plot_middle_bars(
    adjusted: DataFrame,
    middle: float,
    kwargs: dict[str, Any],
) -> Axes:
    """Plot the middle (typically 80%) of the data as a bar."""
    q = calc_quantiles(middle)
    lo_hi: DataFrame = adjusted.quantile(q=q).T  # get the middle section of data
    span = 1.15
    space = 0.2
    low = min(adjusted.iloc[-1].min(), lo_hi.min().min(), -span) - space
    high = max(adjusted.iloc[-1].max(), lo_hi.max().max(), span) + space
    kwargs["xlim"] = (low, high)  # update the kwargs with the xlim
    ax, _ = get_axes(**kwargs)
    ax.barh(
        y=lo_hi.index,
        width=lo_hi[q[1]] - lo_hi[q[0]],
        left=lo_hi[q[0]],
        color="#bbbbbb",
        label=f"Middle {middle * 100:0.0f}% of prints",
    )
    return ax


def plot_latest_datapoint(
    ax: Axes,
    original: DataFrame,
    adjusted: DataFrame,
    f_size: int | str,
) -> None:
    """Add the latest datapoints to the summary plot."""
    ax.scatter(adjusted.iloc[-1], adjusted.columns, color="darkorange", label="Latest")
    f_size = 10
    row = adjusted.index[-1]
    for col_num, col_name in enumerate(original.columns):
        x = float(adjusted.at[row, col_name])
        ax.text(
            x=x,
            y=col_num,
            s=f"{x:.{2 if x < 1 else 1}f}",
            ha="center",
            va="center",
            size=f_size,
        )


def label_extremes(
    ax: Axes,
    data: tuple[DataFrame, DataFrame],
    plot_type: str,
    f_size: int | str,
    kwargs: dict[str, Any],  # must be a dictionary, not a splat
) -> None:
    """Label the extremes in the scaled plots."""
    original, adjusted = data
    low, high = kwargs["xlim"]
    ax.set_xlim(low, high)  # set the x-axis limits
    if plot_type == ZSCALED:
        ax.scatter(
            adjusted.median(),
            adjusted.columns,
            color="darkorchid",
            marker="x",
            s=5,
            label="Median",
        )
        for col_num, col_name in enumerate(original.columns):
            ax.text(
                low,
                col_num,
                f" {original[col_name].min():.2f}",
                ha="left",
                va="center",
                size=f_size,
            )
            ax.text(
                high,
                col_num,
                f"{original[col_name].max():.2f} ",
                ha="right",
                va="center",
                size=f_size,
            )


def horizontal_bar_plot(
    original: DataFrame,
    adjusted: DataFrame,
    middle: float,
    plot_type: str,
    kwargs: dict[str, Any],  # must be a dictionary, not a splat
) -> Axes:
    """Plot horizontal bars for the middle of the data."""
    # kwargs is a dictionary, not a splat
    # so that we can pass it to the Axes object and
    # set the x-axis limits.

    ax = plot_middle_bars(adjusted, middle, kwargs)
    f_size = "x-small"
    plot_latest_datapoint(ax, original, adjusted, f_size)
    label_extremes(ax, data=(original, adjusted), plot_type=plot_type, f_size=f_size, kwargs=kwargs)

    return ax


def label_x_axis(plot_from: int | Period, label: str | None, plot_type: str, ax: Axes, df: DataFrame) -> None:
    """Label the x-axis for the plot."""
    start: Period = plot_from if isinstance(plot_from, Period) else df.index[plot_from]
    if label is not None:
        if not label:
            if plot_type == ZSCORES:
                label = f"Z-scores for prints since {label_period(start)}"
            else:
                label = f"-1 to 1 scaled z-scores since {label_period(start)}"
        ax.set_xlabel(label)


def mark_reference_lines(plot_type: str, ax: Axes) -> None:
    """Mark the reference lines for the plot."""
    if plot_type == ZSCALED:
        ax.axvline(-1, color="#555555", linewidth=0.5, linestyle="--", label="-1")
        ax.axvline(1, color="#555555", linewidth=0.5, linestyle="--", label="+1")
    elif plot_type == ZSCORES:
        ax.axvline(0, color="#555555", linewidth=0.5, linestyle="--", label="0")


def plot_the_data(df: DataFrame, **kwargs: Unpack[SummaryKwargs]) -> tuple[Axes, str]:
    """Plot the data as a summary plot.

    Args:
        df: DataFrame - the data to plot.
        kwargs: SummaryKwargs, additional keyword arguments for the plot, including:

    Returns a tuple comprising:
    - ax: Axes object containing the plot.
    - plot_type: type of plot, either 'zscores' or 'zscaled'.

    """
    # get the data, calculate z-scores and scaled scores based on the start period
    verbose = kwargs.pop("verbose", False)
    middle = float(kwargs.pop("middle", 0.8))
    plot_type = kwargs.pop("plot_type", ZSCORES)
    subset, kwargsd = constrain_data(df, **kwargs)
    z_scores, z_scaled = calculate_z(subset, middle, verbose=verbose)

    # plot as required by the plot_types argument
    adjusted = z_scores if plot_type == ZSCORES else z_scaled
    ax = horizontal_bar_plot(subset, adjusted, middle, plot_type, kwargsd)
    ax.tick_params(axis="y", labelsize="small")
    make_legend(ax, legend=kwargsd["legend"])
    ax.set_xlim(kwargsd.get("xlim"))  # provide space for the labels

    return ax, plot_type


# --- public
def summary_plot(data: DataT, **kwargs: Unpack[SummaryKwargs]) -> Axes:
    """Plot a summary of historical data for a given DataFrame.

    Args:x
    - summary: DataFrame containing the summary data. The column names are
      used as labels for the plot.
    - kwargs: additional arguments for the plot, including:

    Returns Axes.
    """
    # --- check the kwargs
    me = "summary_plot"
    report_kwargs(caller=me, **kwargs)
    validate_kwargs(schema=SummaryKwargs, caller=me, **kwargs)

    # --- check the data
    data = check_clean_timeseries(data, me)
    if not isinstance(data, DataFrame):
        raise TypeError("data must be a pandas DataFrame for summary_plot()")
    df = DataFrame(data)  # syntactic sugar for type hinting

    # --- legend
    kwargs["legend"] = kwargs.get(
        "legend",
        {
            # put the legend below the x-axis label
            "loc": "upper center",
            "fontsize": "xx-small",
            "bbox_to_anchor": (0.5, -0.125),
            "ncol": 4,
        },
    )

    # --- and plot it ...
    ax, plot_type = plot_the_data(df, **kwargs)
    label_x_axis(
        kwargs.get("plot_from", 0),
        label=kwargs.get("xlabel", ""),
        plot_type=plot_type,
        ax=ax,
        df=df,
    )
    mark_reference_lines(plot_type, ax)

    return ax
