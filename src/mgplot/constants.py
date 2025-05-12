# --- constants - default settings
_DataT = TypeVar("_DataT", Series, DataFrame)  # python 3.11+

# no need to set plotstyle elsewhere
plt.style.use("fivethirtyeight")
mpl.rcParams["font.size"] = 12


DEFAULT_FILE_TYPE: Final[str] = "png"
DEFAULT_FIG_SIZE: Final[tuple[float, float]] = (9.0, 4.5)
DEFAULT_DPI: Final[int] = 300
DEFAULT_CHART_DIR: Final[str] = "."

COLOR_AMBER: Final[str] = "darkorange"
COLOR_BLUE: Final[str] = "mediumblue"
COLOR_RED: Final[str] = "#dd0000"
COLOR_GREEN: Final[str] = "mediumseagreen"

NARROW_WIDTH: Final[float] = 0.75
WIDE_WIDTH: Final[float] = 2.0
LEGEND_FONTSIZE: Final[str] = "small"
LEGEND_SET: Final[dict[str, Any]] = {"loc": "best", "fontsize": LEGEND_FONTSIZE}

