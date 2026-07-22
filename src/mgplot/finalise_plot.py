"""Functions to finalise and save plots to the file system."""

import re
import unicodedata
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final, NotRequired, Unpack

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory
from pandas import Period, PeriodIndex

from mgplot.annotation_utils import resolve_annotation_collisions
from mgplot.axis_utils import get_period_axes, refresh_period_labels, register_period_axes
from mgplot.keyword_checking import BaseKwargs, report_kwargs, validate_kwargs
from mgplot.settings import get_setting

# --- constants
ME: Final[str] = "finalise_plot"
MAX_FILENAME_LENGTH: Final[int] = 150
DEFAULT_MARGIN: Final[float] = 0.02
TIGHT_LAYOUT_PAD: Final[float] = 1.1
FOOTNOTE_FONTSIZE: Final[int] = 8
FOOTNOTE_FONTSTYLE: Final[str] = "italic"
FOOTNOTE_COLOR: Final[str] = "#999999"
ZERO_LINE_WIDTH: Final[float] = 0.66
ZERO_LINE_COLOR: Final[str] = "#555555"
ZERO_AXIS_ADJUSTMENT: Final[float] = 0.02
DEFAULT_FILE_TITLE_NAME: Final[str] = "plot"
# --- annotated axvline text
VLINE_TEXT_FONTSIZE: Final[str] = "xx-small"
VLINE_TEXT_ROTATION: Final[int] = 90
VLINE_TEXT_OFFSET: Final[float] = 2.0  # points, to the right of the line
VLINE_TEXT_PAD: Final[float] = 0.01  # axes fraction, in from the top/bottom
VLINE_AUTO_BAND: Final[float] = 0.02  # fraction of the x-span sampled either side


class FinaliseKwargs(BaseKwargs):
    """Keyword arguments for the finalise_plot function."""

    # --- value options
    suptitle: NotRequired[str | None]
    title: NotRequired[str | None]
    xlabel: NotRequired[str | None]
    ylabel: NotRequired[str | None]
    xlim: NotRequired[tuple[float | int | Period, float | int | Period] | None]
    ylim: NotRequired[tuple[float, float] | None]
    xticks: NotRequired[list[float | int | Period] | None]
    yticks: NotRequired[list[float] | None]
    xscale: NotRequired[str | None]
    yscale: NotRequired[str | None]
    # --- splat options
    legend: NotRequired[bool | dict[str, Any] | None]
    axhspan: NotRequired[dict[str, Any] | Sequence[dict[str, Any]] | None]
    axvspan: NotRequired[dict[str, Any] | Sequence[dict[str, Any]] | None]
    axhline: NotRequired[dict[str, Any] | Sequence[dict[str, Any]] | None]
    axvline: NotRequired[dict[str, Any] | Sequence[dict[str, Any]] | None]
    # --- options for annotations
    lfooter: NotRequired[str]
    rfooter: NotRequired[str]
    lheader: NotRequired[str]
    rheader: NotRequired[str]
    # --- file/save options
    pre_tag: NotRequired[str]
    tag: NotRequired[str]
    filename: NotRequired[str]
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
    axisbelow: NotRequired[bool]
    dont_save: NotRequired[bool]
    dont_close: NotRequired[bool]
    axes_only: NotRequired[bool]


VALUE_KWARGS = (
    "title",
    "xlabel",
    "ylabel",
    "xlim",
    "ylim",
    "xticks",
    "yticks",
    "xscale",
    "yscale",
)
SPLAT_KWARGS = (
    "axhspan",
    "axvspan",
    "axhline",
    "axvline",
    "legend",  # needs to be last in this tuple
)
HEADER_FOOTER_KWARGS = (
    "lfooter",
    "rfooter",
    "lheader",
    "rheader",
)


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """Convert a string to a safe filename.

    Args:
        filename: The string to convert to a filename
        max_length: Maximum length for the filename

    Returns:
        A safe filename string

    """
    if not filename:
        return "untitled"

    # Normalize unicode characters (e.g., é -> e)
    filename = unicodedata.normalize("NFKD", filename)

    # Remove non-ASCII characters
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    filename = filename.lower()

    # Replace spaces and other separators with hyphens
    filename = re.sub(r"[\s\-_]+", "-", filename)

    # Remove unsafe characters, keeping only alphanumeric and hyphens
    filename = re.sub(r"[^a-z0-9\-]", "", filename)

    # Remove leading/trailing hyphens and collapse multiple hyphens
    filename = re.sub(r"^-+|-+$", "", filename)
    filename = re.sub(r"-+", "-", filename)

    # Truncate to max length
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip("-")

    # Ensure we have a valid filename
    return filename or "untitled"


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


def apply_value_kwargs(axes: Axes, value_kwargs_: Sequence[str], **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set matplotlib elements by name using Axes.set().

    Tricky: some plotting functions may set the xlabel or ylabel.
    So ... we will set these if a setting is explicitly provided. If no
    setting is provided, we will set to None if they are not already set.
    If they have already been set, we will not change them.

    """
    # --- preliminary
    function: dict[str, Callable[[], str]] = {
        "xlabel": axes.get_xlabel,
        "ylabel": axes.get_ylabel,
        "title": axes.get_title,
    }

    def fail() -> str:
        return ""

    # --- loop over potential value settings
    for setting in value_kwargs_:
        value = _convert_period_value(axes, setting, kwargs.get(setting))
        if setting in kwargs:
            # deliberately set, so we will action
            axes.set(**{setting: value})
            continue
        required_to_set = ("title", "xlabel", "ylabel")
        if setting not in required_to_set:
            # not set - and not required - so we can skip
            continue

        # we will set these 'required_to_set' ones
        # provided they are not already set
        already_set = function.get(setting, fail)()
        if already_set and value is None:
            continue

        # if we get here, we will set the value (implicitly to None)
        axes.set(**{setting: value})


_SplatValue = bool | dict[str, Any] | Sequence[dict[str, Any]] | None

# Keys in each splat-method's kwargs that are x-axis coordinates — when the
# plot uses a PeriodIndex the axis is mapped to Period ordinals, so a Period
# passed here must be converted to its ordinal for matplotlib.
_PERIOD_COORD_KEYS: Final[dict[str, tuple[str, ...]]] = {
    "axvline": ("x",),
    "axvspan": ("xmin", "xmax"),
}


def _convert_period_coords(axes: Axes, method_name: str, item: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of item with any Period x-coordinates replaced by ordinals.

    If the axes was period-mapped by mgplot, the Period's freq must match the
    axes' stashed freq — otherwise the ordinals live in different spaces.
    On an axes with no stash we trust the programmer and just take .ordinal.
    """
    keys = _PERIOD_COORD_KEYS.get(method_name)
    if not keys:
        return item
    stash = get_period_axes(axes)
    stashed_freq = stash[0] if stash is not None else None
    converted = dict(item)
    for key in keys:
        val = converted.get(key)
        if isinstance(val, Period):
            if stashed_freq is not None and val.freqstr != stashed_freq:
                raise ValueError(
                    f"{method_name} Period freq {val.freqstr!r} does not match axes freq {stashed_freq!r}",
                )
            if stashed_freq is not None:
                # Widen the stash so later label refresh covers this coordinate,
                # even if it falls outside the plotted data's ordinal range.
                register_period_axes(axes, PeriodIndex([val]))
            converted[key] = val.ordinal
    return converted


# Value-kwargs whose entries are x-axis coordinates — like axvline/axvspan, a
# Period passed here must be converted to its ordinal on a period-mapped axes.
_PERIOD_X_VALUE_KWARGS: Final[tuple[str, ...]] = ("xlim", "xticks")


def _convert_period_value(axes: Axes, setting: str, value: object) -> object:
    """Return value with any Period x-coordinates replaced by ordinals.

    xlim is a 2-tuple and xticks a list; either may contain Periods when the
    caller describes the axis in calendar terms. On a period-mapped axes the
    Period freq must match the axes' stashed freq (see register_period_axes).
    Non-x settings, None, and non-Period entries pass through unchanged.
    """
    if setting not in _PERIOD_X_VALUE_KWARGS or not isinstance(value, (tuple, list)):
        return value
    stash = get_period_axes(axes)
    stashed_freq = stash[0] if stash is not None else None
    converted: list[object] = []
    for val in value:
        if isinstance(val, Period):
            if stashed_freq is not None and val.freqstr != stashed_freq:
                raise ValueError(
                    f"{setting} Period freq {val.freqstr!r} does not match axes freq {stashed_freq!r}",
                )
            if stashed_freq is not None:
                # Widen the stash so the later label refresh covers this coordinate.
                register_period_axes(axes, PeriodIndex([val]))
            converted.append(val.ordinal)
        else:
            converted.append(val)
    return tuple(converted) if isinstance(value, tuple) else converted


# --- annotated vertical lines
# "text", "loc" and "text_kwargs" in an axvline dict describe its label rather
# than the line, and are popped before the dict is splatted into ax.axvline().
# loc is a space-separated string mixing a vertical word ("auto"/"top"/"bottom")
# with a side word ("left"/"right"); either may be omitted. The side picks which
# flank of the line the rotated label sits on, VLINE_TEXT_OFFSET points away.
_VLINE_EDGES: Final[tuple[str, ...]] = ("top", "bottom")
_VLINE_SIDES: Final[tuple[str, ...]] = ("left", "right")


def _parse_vline_loc(loc: object) -> tuple[str, str]:
    """Split a loc string into (edge, side), order-free and each optional.

    edge is "auto", "top" or "bottom"; side is "left" or "right". An omitted
    edge falls back to "auto" (choose by the data) and an omitted side to
    "right" (today's placement). Raises on an unrecognised or doubled word --
    each is a typo, not a choice.
    """
    if not isinstance(loc, str):
        raise TypeError(f"axvline 'loc' must be a string, got {type(loc)}")
    edge: str | None = None
    side: str | None = None
    for tok in loc.split():
        if tok == "auto" or tok in _VLINE_EDGES:
            if edge is not None:
                raise ValueError(f"axvline 'loc' names two vertical positions, got {loc!r}")
            edge = tok
        elif tok in _VLINE_SIDES:
            if side is not None:
                raise ValueError(f"axvline 'loc' names two sides, got {loc!r}")
            side = tok
        else:
            raise ValueError(f"axvline 'loc' word {tok!r} not recognised in {loc!r}")
    return edge or "auto", side or "right"


def _pop_vline_text(item: dict[str, Any]) -> tuple[str, str, dict[str, Any]] | None:
    """Remove the label keys from an axvline dict and return them, or None if unlabelled.

    Raises on a bad loc, a non-dict text_kwargs, or label options given
    without any text to place -- each of which is a typo, not a choice.
    """
    text = item.pop("text", None)
    loc = item.pop("loc", "auto")
    text_kwargs = item.pop("text_kwargs", {})

    if text is None or not str(text).strip():
        if loc != "auto" or text_kwargs:
            raise ValueError("axvline 'loc'/'text_kwargs' given without any 'text' to place")
        return None
    _parse_vline_loc(loc)  # validate now; raises on a bad loc string
    if not isinstance(text_kwargs, dict):
        raise TypeError(f"axvline 'text_kwargs' must be a dict, got {type(text_kwargs)}")
    return str(text), loc, text_kwargs


def _data_y_extent(axes: Axes, x: float) -> tuple[float, float] | None:
    """Return the (min, max) y of plotted data in a narrow x-band around x.

    A rotated label occupies only a sliver of the x-axis, so a narrow band is
    what the eye actually judges. Lines are matched by transform identity:
    axhline/axvline use blended transforms, so this skips them and measures
    only real data. Rectangles cover bar plots; axvspan/axhspan patches are
    likewise blended and skipped. Returns None when nothing is measurable.
    """
    left, right = axes.get_xlim()
    half = abs(right - left) * VLINE_AUTO_BAND
    low, high = x - half, x + half
    found: list[float] = []

    for line in axes.get_lines():
        if not isinstance(line, Line2D) or line.get_transform() is not axes.transData:
            continue
        xdata = np.asarray(line.get_xdata(), dtype=float)
        ydata = np.asarray(line.get_ydata(), dtype=float)
        if xdata.size != ydata.size or xdata.size == 0:
            continue
        wanted = (xdata >= low) & (xdata <= high) & ~np.isnan(ydata)
        if wanted.any():
            found.extend((float(ydata[wanted].min()), float(ydata[wanted].max())))

    for patch in axes.patches:
        if not isinstance(patch, Rectangle) or patch.get_data_transform() is not axes.transData:
            continue
        x0, width = patch.get_x(), patch.get_width()
        y0, height = patch.get_y(), patch.get_height()
        if min(x0, x0 + width) > high or max(x0, x0 + width) < low:
            continue
        found.extend((min(y0, y0 + height), max(y0, y0 + height)))

    if not found:
        return None
    return min(found), max(found)


def _auto_vline_loc(axes: Axes, x: float) -> str:
    """Pick the end of the axes with more room between the data and the limit."""
    extent = _data_y_extent(axes, x)
    if extent is None:
        return "top"  # nothing measurable (empty band, or an unrecognised artist)
    data_low, data_high = extent
    bottom_lim, top_lim = axes.get_ylim()
    if top_lim >= bottom_lim:
        top_gap, bottom_gap = top_lim - data_high, data_low - bottom_lim
    else:  # inverted y-axis: values decrease going up the display
        top_gap, bottom_gap = data_low - top_lim, bottom_lim - data_high
    return "top" if top_gap >= bottom_gap else "bottom"


def _annotate_vline(axes: Axes, item: dict[str, Any], line: Line2D, spec: tuple[str, str, dict]) -> None:
    """Place a rotated text label just to one side of a vertical line.

    The side (left/right of the line) comes from loc; the label is anchored
    with x in data coordinates and y in axes coordinates, so it stays pinned
    to the top/bottom of the plot regardless of any later change to the
    y-limits.
    """
    text, loc, text_kwargs = spec
    x = item.get("x", 0)  # matches the matplotlib default for axvline
    edge, side = _parse_vline_loc(loc)
    if edge == "auto":
        edge = _auto_vline_loc(axes, float(x))
    y, valign = (1.0 - VLINE_TEXT_PAD, "top") if edge == "top" else (VLINE_TEXT_PAD, "bottom")
    x_off, halign = (VLINE_TEXT_OFFSET, "left") if side == "right" else (-VLINE_TEXT_OFFSET, "right")

    options: dict[str, Any] = {
        "rotation": VLINE_TEXT_ROTATION,
        "fontsize": VLINE_TEXT_FONTSIZE,
        "color": line.get_color(),
        "ha": halign,
        "va": valign,
    }
    options.update(text_kwargs)
    axes.annotate(
        text,
        xy=(x, y),
        xycoords=blended_transform_factory(axes.transData, axes.transAxes),
        xytext=(x_off, 0),
        textcoords="offset points",
        **options,
    )


def _apply_splat(axes: Axes, method_name: str, value: _SplatValue) -> None:
    """Apply a single splat kwarg, which may be a dict or sequence of dicts."""
    if value is None or value is False:
        return

    if value is True:  # use the global default settings
        value = get_setting(method_name)

    # normalise to a list of dicts
    if isinstance(value, dict):
        value = [value]

    if isinstance(value, Sequence):
        method = getattr(axes, method_name)
        for item in value:
            if not isinstance(item, dict):
                print(f"Warning: expected dict in {method_name} sequence, but got {type(item)}.")
                continue
            converted = _convert_period_coords(axes, method_name, item)
            # _convert_period_coords always copies, so popping is safe here
            spec = _pop_vline_text(converted) if method_name == "axvline" else None
            artist = method(**converted)
            if spec is not None and isinstance(artist, Line2D):
                _annotate_vline(axes, converted, artist, spec)
    else:
        print(f"Warning: expected dict or sequence of dicts for {method_name}, but got {type(value)}.")


def apply_splat_kwargs(axes: Axes, settings: tuple, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set matplotlib elements dynamically using setting_name and splat."""
    for method_name in settings:
        if method_name not in kwargs:
            continue

        if method_name == "legend":
            legend_value = kwargs.get(method_name)
            if isinstance(legend_value, (bool, dict, type(None))):
                make_legend(axes, legend=legend_value)
            else:
                print(f"Warning: expected bool, dict, or None for legend, but got {type(legend_value)}.")
            continue

        value = kwargs.get(method_name)
        if value is None or isinstance(value, (bool, dict, Sequence)):
            _apply_splat(axes, method_name, value)
        else:
            print(f"Warning: expected dict or sequence of dicts for {method_name}, but got {type(value)}.")


def apply_annotations(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Set figure size and apply chart annotations.

    No-op when axes_only=True: the work here is all figure-level (resize,
    corner text) and would stomp on other panels in a multi-axes figure.
    """
    if kwargs.get("axes_only"):
        return
    fig = axes.figure
    fig_size = kwargs.get("figsize", get_setting("figsize"))
    if not isinstance(fig, SubFigure):
        fig.set_size_inches(*fig_size)

    annotations = {
        "rfooter": (0.99, 0.001, "right", "bottom"),
        "lfooter": (0.01, 0.001, "left", "bottom"),
        "rheader": (0.99, 0.999, "right", "top"),
        "lheader": (0.01, 0.999, "left", "top"),
    }

    for annotation in HEADER_FOOTER_KWARGS:
        if annotation in kwargs:
            x_pos, y_pos, h_align, v_align = annotations[annotation]
            fig.text(
                x_pos,
                y_pos,
                str(kwargs.get(annotation, "")),
                ha=h_align,
                va=v_align,
                fontsize=FOOTNOTE_FONTSIZE,
                fontstyle=FOOTNOTE_FONTSTYLE,
                color=FOOTNOTE_COLOR,
            )


def apply_late_kwargs(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Apply settings found in kwargs, after plotting the data."""
    apply_splat_kwargs(axes, SPLAT_KWARGS, **kwargs)


def apply_kwargs(axes: Axes, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Apply settings found in kwargs."""

    def check_kwargs(name: str) -> bool:
        return name in kwargs and bool(kwargs.get(name))

    apply_value_kwargs(axes, VALUE_KWARGS, **kwargs)
    apply_annotations(axes, **kwargs)

    if check_kwargs("zero_y"):
        bottom, top = axes.get_ylim()
        adj = (top - bottom) * ZERO_AXIS_ADJUSTMENT
        if bottom > -adj:
            axes.set_ylim(bottom=-adj)
        if top < adj:
            axes.set_ylim(top=adj)

    if check_kwargs("y0"):
        low, high = axes.get_ylim()
        if low < 0 < high:
            axes.axhline(y=0, lw=ZERO_LINE_WIDTH, c=ZERO_LINE_COLOR)

    if check_kwargs("x0"):
        low, high = axes.get_xlim()
        if low < 0 < high:
            axes.axvline(x=0, lw=ZERO_LINE_WIDTH, c=ZERO_LINE_COLOR)

    if check_kwargs("axisbelow"):
        axes.set_axisbelow(True)


def save_to_file(fig: Figure, **kwargs: Unpack[FinaliseKwargs]) -> None:
    """Save the figure to file."""
    saving = not kwargs.get("dont_save", False)  # save by default
    if not saving:
        return

    try:
        chart_dir = Path(kwargs.get("chart_dir", get_setting("chart_dir")))

        # Ensure directory exists
        chart_dir.mkdir(parents=True, exist_ok=True)

        suptitle = kwargs.get("suptitle", "")
        title = kwargs.get("title", "")
        pre_tag = kwargs.get("pre_tag", "")
        tag = kwargs.get("tag", "")
        name_override = kwargs.get("filename", "")
        name_title = name_override or suptitle or title
        file_title = sanitize_filename(name_title or DEFAULT_FILE_TITLE_NAME)
        file_type = kwargs.get("file_type", get_setting("file_type")).lower()
        dpi = kwargs.get("dpi", get_setting("dpi"))

        # Construct filename components safely
        filename_parts = []
        if pre_tag:
            filename_parts.append(sanitize_filename(pre_tag))
        filename_parts.append(file_title)
        if tag:
            filename_parts.append(sanitize_filename(tag))

        # Join filename parts and add extension
        filename = "-".join(filter(None, filename_parts))
        filepath = chart_dir / f"{filename}.{file_type}"

        fig.savefig(filepath, dpi=dpi)

    except (
        OSError,
        PermissionError,
        FileNotFoundError,
        ValueError,
        RuntimeError,
        TypeError,
        UnicodeError,
    ) as e:
        print(f"Error: Could not save plot to file: {e}")


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
        print(f"Warning: {ME}() called with an empty axes, which was ignored.")
        return

    # --- remember axis-limits should we need to restore thems
    xlim, ylim = axes.get_xlim(), axes.get_ylim()

    # margins
    axes.margins(DEFAULT_MARGIN)
    axes.autoscale(tight=False)  # This is problematic ...

    apply_kwargs(axes, **kwargs)

    # tight layout and save the figure
    fig = axes.figure
    axes_only = kwargs.get("axes_only", False)
    if not axes_only and (suptitle := kwargs.get("suptitle")):
        fig.suptitle(suptitle)
    if kwargs.get("preserve_lims"):
        # restore the original limits of the axes
        axes.set_xlim(xlim)
        axes.set_ylim(ylim)
    if not axes_only and not isinstance(fig, SubFigure):
        fig.tight_layout(pad=TIGHT_LAYOUT_PAD)
    apply_late_kwargs(axes, **kwargs)
    # axvspan/axvline in late_kwargs may have widened xlim beyond what
    # set_labels() last saw; regenerate ticks from the updated view.
    refresh_period_labels(axes)
    # de-collide end-of-line annotations now that the layout/limits are final
    resolve_annotation_collisions(axes)
    legend = axes.get_legend()
    if legend and kwargs.get("remove_legend", False):
        legend.remove()
    if not axes_only and not isinstance(fig, SubFigure):
        save_to_file(fig, **kwargs)

    # show the plot in Jupyter Lab
    if not axes_only and kwargs.get("show"):
        plt.show()

    # And close - the figure this axes belongs to, not pyplot's current figure
    if not axes_only and not kwargs.get("dont_close", False):
        root = fig
        while isinstance(root, SubFigure):
            root = root.figure
        plt.close(root)
