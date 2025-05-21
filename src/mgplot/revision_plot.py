"""
revision_plot.py
Plot ABS revisions to estimates over time.
"""

# --- imports
from pandas import DataFrame, Series
import numpy as np


from mgplot.finalise_plot import finalise_plot, FINALISE_KW_TYPES
from mgplot.utilities import annotate_series, validate_kwargs
from mgplot.kw_type_checking import report_kwargs


# --- constants
ROUNDING = "rounding"
REVISION_KW_TYPES: dict[str, type | tuple[type, ...]] = {
    ROUNDING: (int, bool),
}


# --- functions
def revision_plot(data: DataFrame, units: str, recent=18, **kwargs) -> None:
    """
    Plot the revisions to ABS data.

    Arguments
    data: pd.DataFrame - the data to plot, the DataFrame has a
        column for each data revision
    units: str - the units for the data (Note: you may need to
        recalibrate the units for the y-axis)
    recent: int - the number of recent data points to plot
    kwargs : dict : mostly additional arguments to pass to finalise_plot(),
        but can include:
        -   rounding: int | bool - if True apply default rounding, otherwise
            apply int rounding.
    """

    report_kwargs(kwargs, called_from="revision_plot")
    expected = REVISION_KW_TYPES | FINALISE_KW_TYPES
    validate_kwargs(kwargs, expected, "revision_plot")

    # focis on the data we wasnt to plot
    repository = data[data.columns[::-1]].tail(recent)

    # plot the data
    axes = repository.plot()

    # Annotate the last value in each series ...
    rounding: int | bool = kwargs.pop(ROUNDING, True)
    for c in repository.columns:
        col: Series = repository.loc[:, c].dropna()
        annotate_series(col, axes, color="#222222", rounding=rounding, fontsize="small")

    # change the line width for new data
    how_far_back = len(data.columns)
    linewidth = (np.arange(0, how_far_back) / (how_far_back - 1)) + 1
    for line, width in zip(axes.get_lines(), linewidth):
        line.set_linewidth(width)

    finalise_plot(
        axes,
        ylabel=f"{units}",
        **kwargs,
    )
