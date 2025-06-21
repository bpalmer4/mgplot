"""Functions to finalise and save plots to the file system."""

import re
from collections.abc import Callable, Sequence
from typing import Any, Final, NotRequired, Unpack

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.pyplot import Axes, Figure

from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting

# --- constants
ME: Final[str] = "finalise_plot"


class FinaliseKwargs(BaseKwargs):
    """Keyword arguments for the finalise_plot function."""

    # --- value options
    title: NotRequired[str | None]
    xlabel: NotRequired[str | None]
    ylabel: NotRequired[str | None]
    xlim: NotRequired[tuple[float, float] | None]
    ylim: NotRequired[tuple[float, float] | None]
    xticks: NotRequired[list[float] | None]
    yticks: NotRequired[list[float] | None]
    x_scale: NotRequired[str | None]
    y_scale: NotRequired[str | None]
    # --- splat options
    legend: NotRequired[bool | dict[str, Any] | None]
    axhspan: NotRequired[dict[str, Any]]
    axvspan: NotRequired[dict[str, Any]]
    axhline: NotRequired[dict[str, Any]]
    axvline: NotRequired[dict[str, Any]]
    # --- options for annotations
    lfooter: NotRequired[str]
    rfooter: NotRequired[str]
    lheader: NotRequired[str]
    rheader: NotRequired[str]
    # --- file/save options
    pre_tag: NotRequired[str]
    tag: NotRequired[str]
    chart_dir: NotRequired[str]
    file_type: NotRequired[str]
    dpi: NotRequired[int]
    figsize: NotRequired[tuple[float, float]]
    show: NotRequired[bool]
    # --- other options
    preserve_lims: NotRequired[bool]
    remove_legend: NotRequired[bool]
    zero_y: NotRequired[bool]
    y0: NotRequired[bool]
    x0: NotRequired[bool]
    dont_save: NotRequired[bool]
    dont_close: NotRequired[bool]


value_kwargs = (
    "title",
    "xlabel",
    "ylabel",
    "xlim",
    "ylim",
    "xticks",
    "yticks",
    "x_scale",
    "y_scale",
)
splat_kwargs = (
    "legend",
    "axhspan",
    "axvspan",
    "axhline",
    "axvline",
)
annotation_kwargs = (
    "lfooter",
    "rfooter",
    "lheader",
    "rheader",
)


# filename limitations - regex used to map the plot title to a filename
_remove = re.compile(r"[^0-9A-Za-z]")  # sensible file names from alphamum title
_reduce = re.compile(r"[-]+")  # eliminate multiple hyphens


def make_legend(axes: Axes, *, legend: None | bool | dict[str, Any]) -> None:
    """Create a legend for the plot."""
    if legend is None or legend is False:
        return

    if legend is True:  # use the global default settings
        legend = get_setting("legend")

    if isinstance(legend, dict):
        axes.legend(**legend)
        return

    print(f"Warning: expected dict argument for legend, but got {type(legend)}.")


def apply_value_kwargs(axes: Axes, settings: Sequence[str], **kwargs) -> None:
    """Set matplotlib elements by name using Axes.set()."""
    for setting in settings:
        value = kwargs.get(setting)
        if value is None and setting not in ("title", "xlabel", "ylabel"):
            continue
        function: dict[str, Callable[[], str]] = {
            "xlabel": axes.get_xlabel,
            "ylabel": axes.get_ylabel,
            "title": axes.get_title,
        }

        def fail() -> str:
            return ""

        if value is None and function.get(setting, fail)():
            # setting is already set
            continue
        axes.set(**{setting: value})


def apply_splat_kwargs(axes: Axes, settings: tuple, **kwargs) -> None:
    """Set matplotlib elements dynamically using setting_name and splat."""
    for method_name in settings:
        if method_name in kwargs:
            if method_name == "legend":
                # special case for legend
                make_legend(axes, legend=kwargs[method_name])
                continue

            if kwargs[method_name] is None or kwargs[method_name] is False:
                continue

            if kwargs[method_name] is True:  # use the global default settings
                kwargs[method_name] = get_setting(method_name)

            # splat the kwargs to the method
            if isinstance(kwargs[method_name], dict):
                method = getattr(axes, method_name)
                method(**kwargs[method_name])
            else:
                print(
                    f"Warning expected dict argument for {method_name} but got {type(kwargs[method_name])}.",
                )


def apply_annotations(axes: Axes, **kwargs) -> None:
    """Set figure size and apply chart annotations."""
    fig = axes.figure
    fig_size = kwargs.get("figsize", get_setting("figsize"))
    if not isinstance(fig, mpl.figure.SubFigure):
        fig.set_size_inches(*fig_size)

    annotations = {
        "rfooter": (0.99, 0.001, "right", "bottom"),
        "lfooter": (0.01, 0.001, "left", "bottom"),
        "rheader": (0.99, 0.999, "right", "top"),
        "lheader": (0.01, 0.999, "left", "top"),
    }

    for annotation in annotation_kwargs:
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


def apply_late_kwargs(axes: Axes, **kwargs) -> None:
    """Apply settings found in kwargs, after plotting the data."""
    apply_splat_kwargs(axes, splat_kwargs, **kwargs)


def apply_kwargs(axes: Axes, **kwargs) -> None:
    """Apply settings found in kwargs."""

    def check_kwargs(name: str) -> Any:
        return name in kwargs and kwargs[name]

    apply_value_kwargs(axes, value_kwargs, **kwargs)
    apply_annotations(axes, **kwargs)

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


def save_to_file(fig: Figure, **kwargs) -> None:
    """Save the figure to file."""
    saving = not kwargs.get("dont_save", False)  # save by default
    if saving:
        chart_dir = kwargs.get("chart_dir", get_setting("chart_dir"))
        if not chart_dir.endswith("/"):
            chart_dir += "/"

        title = kwargs.get("title", "")
        max_title_len = 150  # avoid overly long file names
        shorter = title if len(title) < max_title_len else title[:max_title_len]
        pre_tag = kwargs.get("pre_tag", "")
        tag = kwargs.get("tag", "")
        file_title = re.sub(_remove, "-", shorter).lower()
        file_title = re.sub(_reduce, "-", file_title)
        file_type = kwargs.get("file_type", get_setting("file_type")).lower()
        dpi = kwargs.get("dpi", get_setting("dpi"))
        fig.savefig(f"{chart_dir}{pre_tag}{file_title}-{tag}.{file_type}", dpi=dpi)


# - public functions for finalise_plot()


def finalise_plot(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Finalise and save plots to the file system.

    The filename for the saved plot is constructed from the global
    chart_dir, the plot's title, any specified tag text, and the
    file_type for the plot.

    Args:
        axes: Axes - matplotlib axes object - required
        kwargs: FinaliseKwargs

    """
    # --- check the kwargs
    report_kwargs(caller=ME, **kwargs)
    validate_kwargs(schema=FinaliseKwargs, caller=ME, **kwargs)

    # --- sanity checks
    if len(axes.get_children()) < 1:
        print(f"Warning: {ME}() called with empty axes, which was ignored.")
        return

    # --- remember axis-limits should we need to restore thems
    xlim, ylim = axes.get_xlim(), axes.get_ylim()

    # margins
    axes.margins(0.02)
    axes.autoscale(tight=False)  # This is problematic ...

    apply_kwargs(axes, **kwargs)

    # tight layout and save the figure
    fig = axes.figure
    if kwargs.get("preserve_lims"):
        # restore the original limits of the axes
        axes.set_xlim(xlim)
        axes.set_ylim(ylim)
    if not isinstance(fig, mpl.figure.SubFigure):  # mypy
        fig.tight_layout(pad=1.1)
    apply_late_kwargs(axes, **kwargs)
    legend = axes.get_legend()
    if legend and kwargs.get("remove_legend", False):
        legend.remove()
    if not isinstance(fig, mpl.figure.SubFigure):  # mypy
        save_to_file(fig, **kwargs)

    # show the plot in Jupyter Lab
    if kwargs.get("show"):
        plt.show()

    # And close
    closing = True if "dont_close" not in kwargs else not kwargs["dont_close"]
    if closing:
        plt.close()
