"""Resolve collisions among end-of-line annotation labels.

line_plot() draws a value label at the right-hand end of each plotted line and
registers the label Text artists, their owning Line2D, and the near-end
threshold on the Axes (register_annotations).  finalise_plot() then calls
resolve_annotation_collisions() as a late step -- once the figure has its final
size and axis limits -- so the label bounding boxes can be measured in display
(pixel) coordinates and nudged so they do not overlap each other or the lines.

Algorithm (everything is computed in display/pixel coordinates):

* Each label is classified by the x of its line end: "at-end" (the rightmost
  data point on the whole axes), "near-end" (within ``near_end`` * data-width of
  the right edge) or "interior".
* Every label is first tried at its own line end.  An overlapping label is
  nudged vertically by at most its own height to find a slot clear of both the
  plotted lines (over the label's horizontal span) and the other labels.  A
  label that finds such a slot keeps that local position.
* A near-end / at-end label that cannot be cleared within that nudge is snapped
  across to the rightmost data point and stacked vertically with the other
  end-of-axes labels.
* An interior label that cannot be cleared keeps the candidate position with the
  most clearance -- overlap is accepted rather than moving it off its line end.
* Line avoidance never applies to a label sitting at the last data point: its
  text extends into the right margin where there is no line to clear.
"""

from math import inf
from typing import Any, Final

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure, SubFigure
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import Transform

# A line in display coordinates: (x-pixels, y-pixels) as parallel arrays.
LineDisp = tuple[np.ndarray, np.ndarray]

# --- constants
_AXES_ANNO_ATTR: Final[str] = "_mgplot_annotations"
_GAP_PX: Final[float] = 2.0  # minimum separation between artists (pixels)
_STEP_PX: Final[float] = 1.0  # search step when looking for a clear slot
_SNAP_LIMIT_PX: Final[float] = 1.0e4  # effectively-unbounded search at the right edge
_SPAN_SAMPLES: Final[int] = 5  # samples of a line across a label's x-span
_X_EPS: Final[float] = 1.0e-9  # fraction-of-span tolerance for "at the last point"


# --- registration (mirrors the period-axes stash in axis_utils)
def register_annotations(
    axes: Axes,
    pairs: list[tuple[Text, Line2D | None]],
    lines: list[Line2D],
    near_end: float,
) -> None:
    """Stash end-of-line annotation artists on an Axes for later de-collision.

    Args:
        axes: the Axes the labels were drawn on.
        pairs: (label Text, the Line2D it annotates) for each annotated series.
        lines: every data Line2D on the axes (obstacles for interior labels).
        near_end: labels whose line end is within this fraction of the data
            width from the right edge are snapped to the edge when they cannot
            be placed locally.

    """
    if not pairs:
        return
    stash: dict[str, Any] = getattr(axes, _AXES_ANNO_ATTR, None) or {"pairs": [], "lines": []}
    stash["pairs"].extend(pairs)
    known = {id(ln) for ln in stash["lines"]}
    stash["lines"].extend(ln for ln in lines if id(ln) not in known)
    stash["near_end"] = near_end
    setattr(axes, _AXES_ANNO_ATTR, stash)


def get_annotations(axes: Axes) -> dict[str, Any] | None:
    """Return the stashed annotation artists for an axes, or None."""
    return getattr(axes, _AXES_ANNO_ATTR, None)


# --- private helpers (all in display coordinates)
def _line_ys_in_span(x0: float, x1: float, line_disps: list[LineDisp]) -> list[float]:
    """Return display y-values of each line sampled across the [x0, x1] strip."""
    ys: list[float] = []
    sample_x = np.linspace(x0, x1, _SPAN_SAMPLES)
    for px, py in line_disps:
        sx = sample_x[(sample_x >= px[0]) & (sample_x <= px[-1])]
        if sx.size:
            ys.extend(np.interp(sx, px, py).tolist())
    return ys


def _hits_line(lab: dict[str, Any], yc: float, line_disps: list[LineDisp]) -> bool:
    """Return True if a label centred at yc overlaps any line within its x-span."""
    half = lab["h"] / 2.0 + _GAP_PX
    return any(yc - half <= y <= yc + half for y in _line_ys_in_span(lab["x0"], lab["x1"], line_disps))


def _hits_label(lab: dict[str, Any], yc: float, placed: list[dict[str, Any]]) -> bool:
    """Return True if a label centred at yc overlaps any already-placed label."""
    for p in placed:
        if lab["x1"] <= p["x0"] or p["x1"] <= lab["x0"]:
            continue  # no horizontal overlap
        if abs(yc - p["yc"]) < (lab["h"] + p["h"]) / 2.0 + _GAP_PX:
            return True
    return False


def _clearance(
    lab: dict[str, Any],
    yc: float,
    placed: list[dict[str, Any]],
    line_disps: list[LineDisp],
) -> float:
    """Signed gap (px) from a label at yc to its nearest obstacle (higher is better)."""
    half = lab["h"] / 2.0
    gap = inf
    for y in _line_ys_in_span(lab["x0"], lab["x1"], line_disps):
        gap = min(gap, abs(yc - y) - half)
    for p in placed:
        if lab["x1"] <= p["x0"] or p["x1"] <= lab["x0"]:
            continue
        gap = min(gap, abs(yc - p["yc"]) - (lab["h"] + p["h"]) / 2.0)
    return gap


def _place_interior(lab: dict[str, Any], placed: list[dict[str, Any]], line_disps: list[LineDisp]) -> None:
    """Place an interior label: nudge <= its height, else accept most clearance."""
    base = lab["yc"]
    if not _hits_line(lab, base, line_disps) and not _hits_label(lab, base, placed):
        return
    best_yc, best_clear = base, _clearance(lab, base, placed, line_disps)
    off = _STEP_PX
    while off <= lab["h"]:
        for cand in (base + off, base - off):
            if not _hits_line(lab, cand, line_disps) and not _hits_label(lab, cand, placed):
                lab["yc"] = cand
                return
            clear = _clearance(lab, cand, placed, line_disps)
            if clear > best_clear:
                best_clear, best_yc = clear, cand
        off += _STEP_PX
    lab["yc"] = best_yc  # cannot clear within +/- height: accept the best overlap


def _free_slot(lab: dict[str, Any], base: float, placed: list[dict[str, Any]]) -> float:
    """Nearest y to base with no label overlap (used at the snapped right edge)."""
    if not _hits_label(lab, base, placed):
        return base
    off = _STEP_PX
    while off <= _SNAP_LIMIT_PX:
        for cand in (base + off, base - off):
            if not _hits_label(lab, cand, placed):
                return cand
        off += _STEP_PX
    return base


def _place_cluster(
    lab: dict[str, Any],
    placed: list[dict[str, Any]],
    line_disps: list[LineDisp],
    right_disp_x: float,
) -> None:
    """Place a near-/at-end label: try local, else snap to the edge and stack."""
    base = lab["yc"]
    if not lab["at_end"]:
        # try to keep it at its own line end, nudging by at most its height
        if not _hits_line(lab, base, line_disps) and not _hits_label(lab, base, placed):
            return
        off = _STEP_PX
        while off <= lab["h"]:
            for cand in (base + off, base - off):
                if not _hits_line(lab, cand, line_disps) and not _hits_label(lab, cand, placed):
                    lab["yc"] = cand
                    return
            off += _STEP_PX
    # snap across to the rightmost data point and stack clear of placed labels
    delta = right_disp_x - lab["x0"]
    lab["x0"] += delta
    lab["x1"] += delta
    lab["snapped"] = True
    lab["yc"] = _free_slot(lab, base, placed)


def _root_figure(axes: Axes) -> Figure:
    """Return the top-level Figure for an axes (drilling through any SubFigure)."""
    fig = axes.figure
    while isinstance(fig, SubFigure):
        fig = fig.figure
    return fig


def _get_renderer(fig: Figure) -> RendererBase | None:
    """Return a renderer for measuring text extents, or None if unavailable."""
    # Agg exposes canvas.get_renderer(); other backends expose Figure._get_renderer().
    renderer = getattr(fig.canvas, "get_renderer", lambda: None)()
    if isinstance(renderer, RendererBase):
        return renderer
    renderer = getattr(fig, "_get_renderer", lambda: None)()
    return renderer if isinstance(renderer, RendererBase) else None


def _line_geometry(
    all_lines: list[Line2D],
    trans: Transform,
) -> tuple[list[LineDisp | None], dict[int, int], float, float, float] | None:
    """Build display-coord line geometry and the axes' data x-extent.

    Returns (line_disps, line_index, right_x, span, right_disp_x), or None when
    no line carries plottable data. Time-series x is monotonic increasing, so
    each line's display arrays are ready for np.interp() sampling.
    """
    line_disps: list[LineDisp | None] = []
    xmaxs: list[float] = []
    xmins: list[float] = []
    for ln in all_lines:
        xd = np.asarray(ln.get_xdata(), dtype=float)
        yd = np.asarray(ln.get_ydata(), dtype=float)
        ok = ~(np.isnan(xd) | np.isnan(yd))
        if not ok.any():
            line_disps.append(None)
            continue
        xmaxs.append(float(xd[ok].max()))
        xmins.append(float(xd[ok].min()))
        pts = trans.transform(np.column_stack([xd[ok], yd[ok]]))
        line_disps.append((pts[:, 0], pts[:, 1]))
    if not xmaxs:
        return None
    right_x = max(xmaxs)
    span = right_x - min(xmins) if right_x > min(xmins) else 1.0
    right_disp_x = float(trans.transform((right_x, 0.0))[0])
    line_index = {id(ln): i for i, ln in enumerate(all_lines)}
    return line_disps, line_index, right_x, span, right_disp_x


def _build_labels(
    pairs: list[tuple[Text, Line2D | None]],
    renderer: RendererBase,
    line_index: dict[int, int],
    edge: tuple[float, float, float],
) -> list[dict[str, Any]]:
    """Measure each annotation and record its display box and edge classification.

    ``edge`` is (right_x, span, near_end) in data coordinates / fraction.
    """
    right_x, span, near_end = edge
    labels: list[dict[str, Any]] = []
    for text, own in pairs:
        if not text.get_text().strip():
            continue
        bb = text.get_window_extent(renderer=renderer)
        x_data = float(text.get_position()[0])
        labels.append(
            {
                "t": text,
                "x_data": x_data,
                "x0": bb.x0,
                "x1": bb.x1,
                "yc": (bb.y0 + bb.y1) / 2.0,
                "h": bb.height,
                "own": line_index.get(id(own), -1),
                "at_end": abs(right_x - x_data) <= _X_EPS * span,
                "near": (right_x - x_data) <= near_end * span,
                "snapped": False,
            },
        )
    return labels


# --- public entry point
def resolve_annotation_collisions(axes: Axes) -> None:
    """Reposition stashed end-of-line labels so they do not collide.

    No-op when the axes has no registered annotations. Called by finalise_plot()
    after the figure layout is final, so that text bounding boxes measured here
    match what is saved.
    """
    stash = get_annotations(axes)
    if stash is None:
        return

    fig = _root_figure(axes)
    fig.canvas.draw()  # realise the final layout so extents are correct
    renderer = _get_renderer(fig)
    if renderer is None:
        return
    trans = axes.transData

    geometry = _line_geometry(stash["lines"], trans)
    if geometry is None:
        return
    line_disps, line_index, right_x, span, right_disp_x = geometry

    labels = _build_labels(stash["pairs"], renderer, line_index, (right_x, span, stash["near_end"]))
    if not labels:
        return

    def others(lab: dict[str, Any]) -> list[LineDisp]:
        """Return line geometry excluding the label's own line (it ends at the anchor)."""
        return [ld for i, ld in enumerate(line_disps) if ld is not None and i != lab["own"]]

    # --- place interior labels first, then the right-edge cluster
    placed: list[dict[str, Any]] = []
    interior = sorted((lab for lab in labels if not lab["near"]), key=lambda lab: lab["yc"])
    cluster = sorted((lab for lab in labels if lab["near"]), key=lambda lab: (-lab["x_data"], lab["yc"]))
    for lab in interior:
        _place_interior(lab, placed, others(lab))
        placed.append(lab)
    for lab in cluster:
        _place_cluster(lab, placed, others(lab), right_disp_x)
        placed.append(lab)

    # --- write the new positions back in data coordinates
    inv = trans.inverted()
    for lab in labels:
        x_disp = right_disp_x if lab["snapped"] else float(trans.transform((lab["x_data"], 0.0))[0])
        _, y_data = inv.transform((x_disp, lab["yc"]))
        lab["t"].set_y(y_data)
        if lab["snapped"]:
            lab["t"].set_x(right_x)
