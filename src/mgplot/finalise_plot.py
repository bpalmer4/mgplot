"""
finalise_plot.py:
This module provides a function to finalise and save plots to the
file system. It is used to publish plots.
"""

# --- imports
# from typing import Any
import re
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes, Figure
import matplotlib.dates as mdates

from mgplot.settings import get_setting
from mgplot.kw_type_checking import (
    report_kwargs,
    validate_expected,
    ExpectedTypeDict,
    #    limit_kwargs,
    validate_kwargs,
)


# --- constants
# filename limitations - regex used to map the plot title to a filename
_remove = re.compile(r"[^0-9A-Za-z]")  # sensible file names from alphamum title
_reduce = re.compile(r"[-]+")  # eliminate multiple hyphens

# map of the acceptable kwargs for finalise_plot()
# make sure "legend" is last in the _splat_kwargs tuple ...
_splat_kwargs = ("axhspan", "axvspan", "axhline", "axvline", "legend")
_value_must_kwargs = ("title", "xlabel", "ylabel")
_value_may_kwargs = ("ylim", "xlim", "yscale", "xscale")
_value_kwargs = _value_must_kwargs + _value_may_kwargs
_annotation_kwargs = ("lfooter", "rfooter", "lheader", "rheader")

_file_kwargs = ("pre_tag", "tag", "chart_dir", "file_type", "dpi")
_fig_kwargs = ("figsize", "show")
_oth_kwargs = (
    "zero_y",
    "y0",
    "x0",
    "dont_save",
    "dont_close",
    "concise_dates",
    "verbose",  # special case for testing
)
_ACCEPTABLE_KWARGS = frozenset(
    _value_kwargs
    + _splat_kwargs
    + _file_kwargs
    + _annotation_kwargs
    + _fig_kwargs
    + _oth_kwargs
)

FINALISE_KW_TYPES: ExpectedTypeDict = {
    # - value kwargs
    "title": (str, type(None)),
    "xlabel": (str, type(None)),
    "ylabel": (str, type(None)),
    "ylim": (tuple, (float, int), type(None)),
    "xlim": (tuple, (float, int), type(None)),
    "yscale": (str, type(None)),
    "xscale": (str, type(None)),
    # - splat kwargs
    "legend": (dict, (str, (int, float, str)), bool, type(None)),
    "axhspan": (dict, (str, (int, float, str)), type(None)),
    "axvspan": (dict, (str, (int, float, str)), type(None)),
    "axhline": (dict, (str, (int, float, str)), type(None)),
    "axvline": (dict, (str, (int, float, str)), type(None)),
    # - file kwargs
    "pre_tag": str,
    "tag": str,
    "chart_dir": str,
    "file_type": str,
    "dpi": int,
    # - fig kwargs
    "figsize": (tuple, (float, int)),
    "show": bool,
    # - annotation kwargs
    "lfooter": str,
    "rfooter": str,
    "lheader": str,
    "rheader": str,
    # - Other kwargs
    "zero_y": bool,
    "y0": bool,
    "x0": bool,
    "dont_save": bool,
    "dont_close": bool,
    "concise_dates": bool,
    "verbose": bool,  # special case for testing
}
validate_expected(FINALISE_KW_TYPES, "finalise_plot")


def _internal_consistency_kwargs():
    """Quick check to ensure that the kwargs checkers are consistent."""

    bad = False
    for k in FINALISE_KW_TYPES:
        if k not in _ACCEPTABLE_KWARGS:
            bad = True
            print(f"Key {k} in FINALISE_KW_TYPES but not _ACCEPTABLE_KWARGS")

    for k in _ACCEPTABLE_KWARGS:
        if k not in FINALISE_KW_TYPES:
            bad = True
            print(f"Key {k} in _ACCEPTABLE_KWARGS but not FINALISE_KW_TYPES")

    if bad:
        raise RuntimeError(
            "Internal error: _ACCEPTABLE_KWARGS and FINALISE_KW_TYPES are inconsistent."
        )


_internal_consistency_kwargs()


# - private utility functions for finalise_plot()


def _apply_value_kwargs(axes: Axes, settings: tuple, **kwargs) -> None:
    """Set matplotlib elements by name using Axes.set()."""

    for setting in settings:
        value = kwargs.get(setting, None)
        if value is None and setting not in _value_must_kwargs:
            continue
        axes.set(**{setting: value})


def _apply_splat_kwargs(axes: Axes, settings: tuple, **kwargs) -> None:
    """
    Set matplotlib elements dynamically using setting_name and splat.
    This is used for legend, axhspan, axvspan, axhline, and axvline.
    These can be ignored if not in kwargs, or set to None in kwargs.
    """

    for method_name in settings:
        if method_name in kwargs and kwargs[method_name] is not None:

            # the legend method is a special case
            if method_name == "legend" and kwargs[method_name] is True:
                # use the global default legend settings
                kwargs[method_name] = get_setting("legend")

            # splat the kwargs to the method
            if isinstance(kwargs[method_name], dict):
                method = getattr(axes, method_name)
                method(**kwargs[method_name])
            else:
                print(
                    f"Warning expected dict argument: {method_name}/"
                    + f"{type(kwargs[method_name])}."
                )


def _apply_annotations(axes: Axes, **kwargs) -> None:
    """Set figure size and apply chart annotations."""

    fig = axes.figure
    fig_size = get_setting("figsize") if "figsize" not in kwargs else kwargs["figsize"]
    if not isinstance(fig, mpl.figure.SubFigure):
        fig.set_size_inches(*fig_size)

    annotations = {
        "rfooter": (0.99, 0.001, "right", "bottom"),
        "lfooter": (0.01, 0.001, "left", "bottom"),
        "rheader": (0.99, 0.999, "right", "top"),
        "lheader": (0.01, 0.999, "left", "top"),
    }

    for annotation in _annotation_kwargs:
        if annotation in kwargs:
            x_pos, y_pos, h_align, v_align = annotations[annotation]
            fig.text(
                x_pos,
                y_pos,
                kwargs[annotation],
                ha=h_align,
                va=v_align,
                fontsize=8,
                fontstyle="italic",
                color="#999999",
            )


def _apply_late_kwargs(axes: Axes, **kwargs) -> None:
    """Apply settings found in kwargs, after plotting the data."""
    _apply_splat_kwargs(axes, _splat_kwargs, **kwargs)


def _apply_kwargs(axes: Axes, **kwargs) -> None:
    """Apply settings found in kwargs."""

    def check_kwargs(name):
        return name in kwargs and kwargs[name]

    _apply_value_kwargs(axes, _value_kwargs, **kwargs)
    _apply_annotations(axes, **kwargs)

    if check_kwargs("zero_y"):
        bottom, top = axes.get_ylim()
        adj = (top - bottom) * 0.02
        if bottom > -adj:
            axes.set_ylim(bottom=-adj)
        if top < adj:
            axes.set_ylim(top=adj)

    if check_kwargs("y0"):
        low, high = axes.get_ylim()
        if low < 0 < high:
            axes.axhline(y=0, lw=0.66, c="#555555")

    if check_kwargs("x0"):
        low, high = axes.get_xlim()
        if low < 0 < high:
            axes.axvline(x=0, lw=0.66, c="#555555")

    if check_kwargs("concise_dates"):
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        axes.xaxis.set_major_locator(locator)
        axes.xaxis.set_major_formatter(formatter)


def _save_to_file(fig: Figure, **kwargs) -> None:
    """Save the figure to file."""

    saving = not kwargs.get("dont_save", False)  # save by default
    if saving:
        chart_dir = kwargs.get("chart_dir", get_setting("chart_dir"))
        if not chart_dir.endswith("/"):
            chart_dir += "/"

        title = "" if "title" not in kwargs else kwargs["title"]
        max_title_len = 150  # avoid overly long file names
        shorter = title if len(title) < max_title_len else title[:max_title_len]
        pre_tag = kwargs.get("pre_tag", "")
        tag = kwargs.get("tag", "")
        file_title = re.sub(_remove, "-", shorter).lower()
        file_title = re.sub(_reduce, "-", file_title)
        file_type = kwargs.get("file_type", get_setting("file_type")).lower()
        dpi = kwargs.get("dpi", get_setting("file_dpi"))
        fig.savefig(f"{chart_dir}{pre_tag}{file_title}-{tag}.{file_type}", dpi=dpi)


# - public functions for finalise_plot()


def finalise_plot(axes: Axes, **kwargs) -> None:
    """
    A function to finalise and save plots to the file system. The filename
    for the saved plot is constructed from the global chart_dir, the plot's title,
    any specified tag text, and the file_type for the plot.

    Arguments:
    - axes - matplotlib axes object - required
    - kwargs
        - title: str - plot title, also used to create the save file name
        - xlabel: str | None - text label for the x-axis
        - ylabel: str | None - label for the y-axis
        - pre_tag: str - text before the title in file name
        - tag: str - text after the title in the file name
          (useful for ensuring that same titled charts do not over-write)
        - chart_dir: str - location of the chart directory
        - file_type: str - specify a file type - eg. 'png' or 'svg'
        - lfooter: str - text to display on bottom left of plot
        - rfooter: str - text to display of bottom right of plot
        - lheader: str - text to display on top left of plot
        - rheader: str - text to display of top right of plot
        - figsize: tuple[float, float] - figure size in inches - eg. (8, 4)
        - show: bool - whether to show the plot or not
        - zero_y: bool - ensure y=0 is included in the plot.
        - y0: bool - highlight the y=0 line on the plot (if in scope)
        - x0: bool - highlights the x=0 line on the plot
        - dont_save: bool - dont save the plot to the file system
        - dont_close: bool - dont close the plot
        - dpi: int - dots per inch for the saved chart
        - legend: bool | dict - if dict, use as the arguments to pass to axes.legend(),
          if True pass the global default arguments to axes.legend()
        - axhspan: dict - arguments to pass to axes.axhspan()
        - axvspan: dict - arguments to pass to axes.axvspan()
        - axhline: dict - arguments to pass to axes.axhline()
        - axvline: dict - arguments to pass to axes.axvline()
        - ylim: tuple[float, float] - set lower and upper y-axis limits
        - xlim: tuple[float, float] - set lower and upper x-axis limits

     Returns:
        - None
    """

    validate_kwargs(kwargs, FINALISE_KW_TYPES, "finalise_plot")
    report_kwargs(kwargs, called_from="finalise_plot")

    # margins
    # axes.use_sticky_margins = False   ### CHECK THIS
    axes.margins(0.02)
    axes.autoscale(tight=False)  # This is problematic ...

    _apply_kwargs(axes, **kwargs)

    # tight layout and save the figure
    fig = axes.figure
    if not isinstance(fig, mpl.figure.SubFigure):  # should never be a SubFigure
        fig.tight_layout(pad=1.1)
        _apply_late_kwargs(axes, **kwargs)
        _save_to_file(fig, **kwargs)

    # show the plot in Jupyter Lab
    if "show" in kwargs and kwargs["show"]:
        plt.show()

    # And close
    closing = True if "dont_close" not in kwargs else not kwargs["dont_close"]
    if closing:
        plt.close()
