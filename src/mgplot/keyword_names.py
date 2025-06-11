"""
keyword_names.py

This module contains all the keyword argument names used in the mgplot
package. These names are used to ensure consistency across the package
and to avoid hardcoding strings in the code.
"""

# === imports
from typing import Final

# === debug names
#   special case, used to print out kwargs at the start of a function
REPORT_KWARGS: Final[str] = "report_kwargs"

# === plot names
# - data treatments
PLOT_FROM: Final[str] = "plot_from"  # used to constrain the data to a starting point
DROPNA: Final[str] = "dropna"

# - plot treatments
AX: Final[str] = "ax"
LABEL_SERIES: Final[str] = "label_series"  # used to label the series in the legend
MAX_TICKS: Final[str] = "max_ticks"  # used to limit the number of ticks on the x-axis

# - plot geometric element (geom)
# line-only geoms
STYLE: Final[str] = "style"  # used for line style, e.g. 'solid', 'dashed', etc.
DRAWSTYLE: Final[str] = "drawstyle"
MARKER: Final[str] = "marker"  # used for line markers, e.g. 'o', 'x', etc.
MARKERSIZE: Final[str] = "markersize"  # used for marker size, e.g. 5, 10, etc.

# - bar-only geoms
STACKED: Final[str] = "stacked"

# common line and bar geoms
WIDTH: Final[str] = "width"
COLOR: Final[str] = "color"
ALPHA: Final[str] = "alpha"

# - annotation of the plot geom (lines: right end point; bars: each one)
ANNOTATE: Final[str] = "annotate"
ROUNDING: Final[str] = "rounding"
FONTSIZE: Final[str] = "fontsize"
FONTNAME: Final[str] = "fontname"
ROTATION: Final[str] = "rotation"
ANNOTATE_COLOR: Final[str] = "annotate_color"  # color for the annotation text
ABOVE: Final[str] = "above"  # used to place the annotation above a bar

# === postcovid_plot names
START_R = "start_r"
END_R = "end_r"

# === run_plot names
THRESHOLD = "threshold"
HIGHLIGHT = "highlight"
DIRECTION = "direction"

# === growth_plot names
# Growth plot is a difficult case, as it combines a
# line plot with a bar plot, and has its own set of arguments.

# line element
LINE_WIDTH: Final[str] = "line_width"
LINE_COLOR: Final[str] = "line_color"
LINE_STYLE: Final[str] = "line_style"
ANNOTATE_LINE: Final[str] = "annotate_line"
LINE_ROUNDING: Final[str] = "line_rounding"
LINE_FONTSIZE: Final[str] = "line_fontsize"
LINE_FONTNAME: Final[str] = "line_fontname"
LINE_ANNO_COLOR: Final[str] = "line_annotate_color"

# bar element
ANNOTATE_BARS: Final[str] = "annotate_bars"
BAR_ROUNDING: Final[str] = "bar_rounding"
BAR_WIDTH: Final[str] = "bar_width"
BAR_COLOR: Final[str] = "bar_color"
BAR_ANNO_COLOR: Final[str] = "bar_annotate_color"
BAR_FONTSIZE: Final[str] = "bar_fontsize"
BAR_FONTNAME: Final[str] = "bar_fontname"
BAR_ROTATION: Final[str] = "bar_rotation"

# === summary_plot names
VERBOSE: Final[str] = "verbose"
MIDDLE: Final[str] = "middle"
PLOT_TYPE: Final[str] = "plot_type"


# === finalise_plot names
# - chart primary labels
TITLE: Final[str] = "title"
XLABEL: Final[str] = "xlabel"
YLABEL: Final[str] = "ylabel"

# - axis limits
Y_LIM: Final[str] = "ylim"
X_LIM: Final[str] = "xlim"
Y_SCALE: Final[str] = "yscale"
X_SCALE: Final[str] = "xscale"

# - chart annotation
LFOOTER: Final[str] = "lfooter"
RFOOTER: Final[str] = "rfooter"
LHEADER: Final[str] = "lheader"
RHEADER: Final[str] = "rheader"

# - matplotlib splat
AXHSPAN: Final[str] = "axhspan"
AXVSPAN: Final[str] = "axvspan"
AXHLINE: Final[str] = "axhline"
AXVLINE: Final[str] = "axvline"
LEGEND: Final[str] = "legend"

# - miscellaneous
ZERO_Y: Final[str] = "zero_y"
Y0: Final[str] = "y0"
X0: Final[str] = "x0"
CONCISE_DATES: Final[str] = "concise_dates"

# - file system / file saving
FIGSIZE: Final[str] = "figsize"
SHOW: Final[str] = "show"
PRESERVE_LIMS: Final[str] = "preserve_lims"
REMOVE_LEGEND: Final[str] = "remove_legend"
PRE_TAG: Final[str] = "pre_tag"
TAG: Final[str] = "tag"
CHART_DIR: Final[str] = "chart_dir"
FILE_TYPE: Final[str] = "file_type"
DPI: Final[str] = "dpi"
DONT_SAVE: Final[str] = "dont_save"
DONT_CLOSE: Final[str] = "dont_close"

# === Abbreviations
# --- geom abbreviations
AB_C: Final[str] = "c"  # color
AB_W: Final[str] = "w"  # width
AB_S: Final[str] = "s"  # style
AB_A: Final[str] = "a"  # alpha

# --- line_plot() abbreviations
AB_M: Final[str] = "m"  # marker
AB_MS: Final[str] = "ms"  # marker size
AB_DS: Final[str] = "ds"  # draw style

# --- specific growth_plot() abbreviations
AB_LS: Final[str] = "ls"  # line style
AB_LW: Final[str] = "lw"  # line width
AB_LC: Final[str] = "lc"  # line color
AB_BW: Final[str] = "bw"  # bar width
AB_BC: Final[str] = "bc"  # bar color

# --- annotation abbreviations
AB_ANNO: Final[str] = "anno"  # annotation
AB_ANNO_C: Final[str] = "anno_c"  # annotation color
AB_ANNO_FN: Final[str] = "anno_fn"  # annotation fontname
AB_ANNO_FS: Final[str] = "anno_fs"  # annotation fontsize

ABBR_DICT: Final[dict[str, str]] = {
    # This dictionary is used to map abbreviations to full names.
    AB_C: COLOR,
    AB_W: WIDTH,
    AB_S: STYLE,
    AB_A: ALPHA,
    AB_M: MARKER,
    AB_MS: MARKERSIZE,
    AB_DS: DRAWSTYLE,
    AB_LS: LINE_STYLE,
    AB_LW: LINE_WIDTH,
    AB_LC: LINE_COLOR,
    AB_BW: BAR_WIDTH,
    AB_BC: BAR_COLOR,
    AB_ANNO: ANNOTATE,
    AB_ANNO_C: ANNOTATE_COLOR,
}
