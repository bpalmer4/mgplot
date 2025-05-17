"""
revision_plot.py
Plot ABS revisions to estimates over time.
"""

from pandas import DataFrame, Series
import numpy as np


from mgplot.finalise_plot import finalise_plot
from mgplot.utilities import annotate_series

# public
def revision_plot(
    data: DataFrame,
    units: str,
    recent=18,
    **kwargs
) -> None:
    """
    Plot the revisions to ABS data.

    Arguments
    data: pd.DataFrame - the data to plot, the DataFrame has a 
        column for each data revision
    units: str - the units for the data (Note: you may need to
        recalibrate the units for the y-axis)
    recent: int - the number of recent data points to plot
    kwargs : dict : additional arguments to pass to finalise_plot().
    """

    # focis on the data we wasnt to plot
    repository = data[data.columns[::-1]].tail(recent)

    # plot the data
    ax = repository.plot()

    # Annotate the last value in each series ...
    for c in repository.columns:
        col: Series = repository.loc[:, c].dropna()
        annotate_series(ax, col, color="#222222", fontsize="small")

    # change the line width for new data
    how_far_back = len(data.columns)
    linewidth = (np.arange(0, how_far_back) / (how_far_back - 1)) + 1
    for line, width in zip(ax.get_lines(), linewidth):
        line.set_linewidth(width)

    finalise_plot(
        ax,
        ylabel=f"{units}",
        **kwargs,
    )
