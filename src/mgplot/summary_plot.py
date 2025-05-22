"""
summary_plot.py:
Produce a summary plot for the data in a given DataFrame.
The data is normalised to z-scores and scaled.
"""

# --- imports
# system imports
from typing import Any

# from collections.abc import Sequence

# analytic third-party imports
from numpy import ndarray, array
from matplotlib.pyplot import Axes, subplots
from pandas import DataFrame, Period, PeriodIndex, read_csv

# local imports
from mgplot.finalise_plot import finalise_plot, FINALISE_KW_TYPES
from mgplot.test import prepare_for_test
from mgplot.kw_type_checking import (
    report_kwargs,
    ExpectedTypeDict,
    validate_expected,
    validate_kwargs,
)

# --- constants
ZSCORES = "zscores"
ZSCALED = "zscaled"

SUMMARY_KW_TYPES: ExpectedTypeDict = {
    "verbose": bool,
    "middle": float,
    "plot_types": (list, (str,)),
}
validate_expected(SUMMARY_KW_TYPES, "summary_plot")


# --- functions
def _calc_quantiles(middle: float) -> ndarray:
    """Calculate the quantiles for the middle of the data."""
    return array([(1 - middle) / 2.0, 1 - (1 - middle) / 2.0])


def _calculate_z(
    original: DataFrame,  # only contains the data points of interest
    middle: float,  # middle proportion of data to highlight (eg. 0.8)
    verbose: bool = False,  # print the summary data
) -> tuple[DataFrame, DataFrame]:
    """Calculate z-scores, scaled z-scores and middle quantiles.
    Return z_scores, z_scaled, q (which are the quantiles for the
    start/end of the middle proportion of data to highlight)."""

    # calculate z-scores, scaled scores and middle quantiles
    z_scores = (original - original.mean()) / original.std()
    z_scaled = (
        # scale z-scores between -1 and +1
        (((z_scores - z_scores.min()) / (z_scores.max() - z_scores.min())) - 0.5)
        * 2
    )
    q_middle = _calc_quantiles(middle)

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
            }
        )
        print(frame)

    return z_scores, z_scaled


def _plot_middle_bars(
    adjusted: DataFrame,
    middle: float,
    kwargs: dict[str, Any],
) -> Axes:
    """Plot the middle (typically 80%) of the data as a bar.
    Note: also sets the x-axis limits in kwargs.
    Return the matplotlib Axes object."""

    q = _calc_quantiles(middle)
    lo_hi: DataFrame = adjusted.quantile(q=q).T  # get the middle section of data
    span = 1.15
    space = 0.15
    low = min(adjusted.iloc[-1].min(), lo_hi.min().min(), -span) - space
    high = max(adjusted.iloc[-1].max(), lo_hi.max().max(), span) + space
    kwargs["xlim"] = (low, high)
    _fig, ax = subplots()
    ax.barh(
        y=lo_hi.index,
        width=lo_hi[q[1]] - lo_hi[q[0]],
        left=lo_hi[q[0]],
        color="#bbbbbb",
        label=f"Middle {middle*100:0.0f}% of prints",
    )
    return ax


def _plot_latest_datapoint(
    ax: Axes,
    original: DataFrame,
    adjusted: DataFrame,
    f_size: int,
) -> None:
    """Add the latest datapoints to the summary plot"""

    ax.scatter(adjusted.iloc[-1], adjusted.columns, color="darkorange")
    f_size = 10
    row = adjusted.index[-1]
    for col_num, col_name in enumerate(original.columns):
        ax.text(
            x=adjusted.at[row, col_name],
            y=col_num,
            s=f"{original.at[row, col_name]:.1f}",
            ha="center",
            va="center",
            size=f_size,
        )


def _label_extremes(
    ax: Axes,
    data: tuple[DataFrame, DataFrame],
    plot_type: str,
    f_size: int,
    kwargs: dict[str, Any],
) -> None:
    """Label the extremes in the scaled plots."""

    original, adjusted = data
    low, high = kwargs["xlim"]
    if plot_type == ZSCALED:
        ax.axvline(-1, color="#555555", linewidth=0.5, linestyle="--")
        ax.axvline(1, color="#555555", linewidth=0.5, linestyle="--")
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
                f" {original[col_name].min():.1f}",
                ha="left",
                va="center",
                size=f_size,
            )
            ax.text(
                high,
                col_num,
                f"{original[col_name].max():.1f} ",
                ha="right",
                va="center",
                size=f_size,
            )


def _horizontal_bar_plot(
    original: DataFrame,
    adjusted: DataFrame,
    middle: float,
    plot_type: str,
    kwargs: dict[str, Any],  # definitely a dictionary and not a splat
) -> Axes:
    """Plot horizontal bars for the middle of the data."""

    ax = _plot_middle_bars(adjusted, middle, kwargs)
    f_size = 10
    _plot_latest_datapoint(ax, original, adjusted, f_size)
    _label_extremes(
        ax, data=(original, adjusted), plot_type=plot_type, f_size=f_size, kwargs=kwargs
    )

    return ax


# public
def summary_plot(
    summary: DataFrame,  # summary data
    start: str | Period,  # starting period for z-score calculation
    **kwargs: Any,
) -> None:
    """Plot a summary of historical data for a given DataFrame.

    Args:
    - summary: DataFrame containing the summary data. The column names are
      used as labels for the plot.
    - start: starting period for z-score calculation.
    - kwargs: additional arguments for the plot, including:
        - verbose: if True, print the summary data.
        - middle: proportion of data to highlight (default is 0.8).
        - plot_types: list of plot types to generate
          (default is ["zscores", "zscaled"]).
        - show: if True, display the plot.
        - ylabel: y-axis label for the plot.
        - legend: legend settings for the plot.
        - x0: if True, set x-axis limits to include 0.


    Returns None.
    """

    # --- check the arguments
    report_kwargs(kwargs, "summary_plot")
    expected_kwargs = FINALISE_KW_TYPES | SUMMARY_KW_TYPES
    validate_kwargs(kwargs, expected_kwargs, "summary_plot")

    # --- optional arguments
    verbose = kwargs.pop("verbose", False)
    middle = kwargs.pop("middle", 0.8)
    plot_types = kwargs.pop("plot_types", [ZSCORES, ZSCALED])

    kwargs["show"] = kwargs.get("show", False)
    kwargs["ylabel"] = kwargs.get("ylabel", None)
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
    kwargs["x0"] = kwargs.get("x0", True)

    # get the data, calculate z-scores and scaled scores based on the start period
    subset = summary.loc[summary.index >= start]
    z_scores, z_scaled = _calculate_z(subset, middle, verbose=verbose)

    # plot as required by the plot_types argument
    kwargs["title"] = kwargs.get("title", f"Summary at {subset.index[-1]}")
    for plot_type in plot_types:

        if plot_type == "zscores":
            adjusted = z_scores
            kwargs["xlabel"] = f"Z-scores for prints since {start}"
            kwargs["x0"] = True
        elif plot_type == "zscaled":
            adjusted = z_scaled
            kwargs["xlabel"] = f"-1 to 1 scaled z-scores since {start}"
        else:
            print(f"Unknown plot type {plot_type}")
            continue

        ax = _horizontal_bar_plot(subset, adjusted, middle, plot_type, kwargs)

        # finalise
        kwargs["pre_tag"] = plot_type
        ax.tick_params(axis="y", labelsize="small")
        fp_kwargs = {k: v for k, v in kwargs.items() if k in FINALISE_KW_TYPES}
        finalise_plot(ax, **fp_kwargs)

        # prepare for next loop
        kwargs.pop("xlabel", None)
        kwargs.pop("x0", None)


# --- test code
if __name__ == "__main__":

    prepare_for_test("summary_plot")

    summary_ = read_csv("./zz-test-data/summary.csv", index_col=0, parse_dates=True)
    summary_.index = PeriodIndex(summary_.index, freq="M")
    summary_plot(
        summary_,
        start=Period("1995-01", freq="M"),
        title="Summary Plot",
        ylabel=None,
        rfooter="Summary Plot",
    )
