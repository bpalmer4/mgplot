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
  end-of-axes labels.  The stack keeps the labels in the same vertical order as
  the line ends they belong to (isotonic placement), so annotations for lines
  that finish close together never read out of order.
* A near-end label that did fit locally but collides with the stack's layout
  joins the stack (repeatedly, as each join re-lays it), rather than being
  jumped over.  Near-end labels nothing collides with are left untouched.
* Stack labels far enough apart not to touch form separate sub-stacks: each
  clears any remaining obstacle on its own, so one pile-up never drags another.
* An interior label that cannot be cleared keeps the candidate position with the
  most clearance -- overlap is accepted rather than moving it off its line end.
* Line avoidance never applies to a label sitting at the last data point: its
  text extends into the right margin where there is no line to clear.

Two caller-set flags change the above:

* ``force_right`` sends every label straight to the snapped stack at the
  rightmost data point, skipping local placement altogether.
* ``leader_lines`` draws a thin leader from a label's anchor (its own line end)
  to the label box, for any label that finished more than half its own height
  away from that anchor.
"""

from dataclasses import dataclass
from math import hypot, inf
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
_LEADER_MIN_FRAC: Final[float] = 0.5  # draw a leader once displaced this many label-heights
_LEADER_LW: Final[float] = 0.7  # leader line width (points)
_LEADER_ALPHA: Final[float] = 0.5  # leader line alpha
_LEADER_ZORDER: Final[float] = 1.5  # under the data lines (matplotlib default zorder 2)


# --- registration (mirrors the period-axes stash in axis_utils)
@dataclass(frozen=True)
class AnnotationOptions:
    """How end-of-line labels should be laid out on an axes.

    Attributes:
        near_end: labels whose line end is within this fraction of the data
            width from the right edge are snapped to the edge when they cannot
            be placed locally.
        force_right: place every label at the rightmost data point, without
            first trying to keep it at its own line end.
        leader_lines: draw a leader from a displaced label back to its anchor.

    """

    near_end: float
    force_right: bool = False
    leader_lines: bool = False


def register_annotations(
    axes: Axes,
    pairs: list[tuple[Text, Line2D | None]],
    lines: list[Line2D],
    options: AnnotationOptions,
) -> None:
    """Stash end-of-line annotation artists on an Axes for later de-collision.

    Args:
        axes: the Axes the labels were drawn on.
        pairs: (label Text, the Line2D it annotates) for each annotated series.
        lines: every data Line2D on the axes (obstacles for interior labels).
        options: the layout settings for this axes; the flags of repeated
            registrations on one axes are OR-ed together.

    """
    if not pairs:
        return
    stash: dict[str, Any] = getattr(axes, _AXES_ANNO_ATTR, None) or {"pairs": [], "lines": []}
    stash["pairs"].extend(pairs)
    known = {id(ln) for ln in stash["lines"]}
    stash["lines"].extend(ln for ln in lines if id(ln) not in known)
    prior: AnnotationOptions | None = stash.get("options")
    stash["options"] = (
        options
        if prior is None
        else AnnotationOptions(
            near_end=options.near_end,
            force_right=options.force_right or prior.force_right,
            leader_lines=options.leader_lines or prior.leader_lines,
        )
    )
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


def _place_cluster_local(
    lab: dict[str, Any],
    placed: list[dict[str, Any]],
    line_disps: list[LineDisp],
) -> bool:
    """Try to keep a near-end label at its own line end; True when it fits there."""
    if lab["at_end"]:
        return False  # already at the right edge: it belongs in the stack
    base = lab["yc"]
    if not _hits_line(lab, base, line_disps) and not _hits_label(lab, base, placed):
        return True
    off = _STEP_PX
    while off <= lab["h"]:
        for cand in (base + off, base - off):
            if not _hits_line(lab, cand, line_disps) and not _hits_label(lab, cand, placed):
                lab["yc"] = cand
                return True
        off += _STEP_PX
    return False


def _isotonic(values: list[float]) -> list[float]:
    """Least-squares fit of a non-decreasing sequence to values (pool adjacent violators)."""
    blocks: list[tuple[float, int]] = []  # (block mean, block size)
    for val in values:
        mean, count = val, 1
        while blocks and blocks[-1][0] > mean:
            prev_mean, prev_count = blocks.pop()
            mean = (prev_mean * prev_count + mean * count) / (prev_count + count)
            count += prev_count
        blocks.append((mean, count))
    out: list[float] = []
    for mean, count in blocks:
        out.extend([mean] * count)
    return out


def _stack_shift(stack: list[dict[str, Any]], ys: list[float], placed: list[dict[str, Any]]) -> float:
    """Smallest whole-stack offset that clears the already-placed labels."""

    def clear(off: float) -> bool:
        return not any(_hits_label(lab, y + off, placed) for lab, y in zip(stack, ys, strict=True))

    if clear(0.0):
        return 0.0
    off = _STEP_PX
    while off <= _SNAP_LIMIT_PX:
        for cand in (off, -off):
            if clear(cand):
                return cand
        off += _STEP_PX
    return 0.0


def _snap_x(lab: dict[str, Any], right_disp_x: float) -> None:
    """Move a label's box across to the rightmost data point."""
    delta = right_disp_x - lab["x0"]
    lab["x0"] += delta
    lab["x1"] += delta
    lab["snapped"] = True


def _sep(lower: dict[str, Any], upper: dict[str, Any]) -> float:
    """Minimum centre-to-centre separation between two stacked labels."""
    return (lower["h"] + upper["h"]) / 2.0 + _GAP_PX


def _stack_layout(stack: list[dict[str, Any]]) -> list[float]:
    """Sort the stack into line-end order and return each label's ideal centre y.

    The vertical order matches the order of the line ends annotated, so labels
    for lines that finish close together never swap.  Within that constraint
    the labels sit as near their own line end as the minimum separation allows.
    """
    stack.sort(key=lambda lab: lab["anchor_yc"])  # bottom-most line end first
    # Subtracting the cumulative minimum separation turns "stay this far apart,
    # in this order" into plain "non-decreasing", which _isotonic() solves.
    cums: list[float] = []
    cum = 0.0
    for i, lab in enumerate(stack):
        if i:
            cum += _sep(stack[i - 1], lab)
        cums.append(cum)
    fitted = _isotonic([lab["anchor_yc"] - c for lab, c in zip(stack, cums, strict=True)])
    return [f + c for f, c in zip(fitted, cums, strict=True)]


def _stack_groups(
    stack: list[dict[str, Any]],
    ys: list[float],
) -> list[tuple[list[dict[str, Any]], list[float]]]:
    """Split a laid-out stack into runs of touching labels (independent sub-stacks)."""
    groups: list[tuple[list[dict[str, Any]], list[float]]] = []
    for i, (lab, y) in enumerate(zip(stack, ys, strict=True)):
        if i and y - ys[i - 1] <= _sep(stack[i - 1], lab) + _STEP_PX:
            groups[-1][0].append(lab)
            groups[-1][1].append(y)
        else:
            groups.append(([lab], [y]))
    return groups


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
                "anchor_x0": bb.x0,  # box left edge before any placement
                "anchor_yc": (bb.y0 + bb.y1) / 2.0,  # the line end this label belongs to
                "own": line_index.get(id(own), -1),
                "at_end": abs(right_x - x_data) <= _X_EPS * span,
                "near": (right_x - x_data) <= near_end * span,
                "snapped": False,
            },
        )
    return labels


def _place_all(
    labels: list[dict[str, Any]],
    line_disps: list[LineDisp | None],
    right_disp_x: float,
    *,
    force_right: bool,
) -> None:
    """Give every label a final display y: interior first, then the right-edge stack."""

    def others(lab: dict[str, Any]) -> list[LineDisp]:
        """Return line geometry excluding the label's own line (it ends at the anchor)."""
        return [ld for i, ld in enumerate(line_disps) if ld is not None and i != lab["own"]]

    placed: list[dict[str, Any]] = []
    interior = [] if force_right else [lab for lab in labels if not lab["near"]]
    cluster = [lab for lab in labels if force_right or lab["near"]]
    for lab in sorted(interior, key=lambda lab: lab["yc"]):
        _place_interior(lab, placed, others(lab))
        placed.append(lab)

    stack: list[dict[str, Any]] = []
    local: list[dict[str, Any]] = []
    for lab in sorted(cluster, key=lambda lab: (-lab["x_data"], lab["yc"])):
        if not force_right and _place_cluster_local(lab, placed, others(lab)):
            placed.append(lab)
            local.append(lab)
        else:
            stack.append(lab)  # laid out together below, so their order is kept
    _resolve_stack(stack, local, placed, right_disp_x)


def _resolve_stack(
    stack: list[dict[str, Any]],
    local: list[dict[str, Any]],
    placed: list[dict[str, Any]],
    right_disp_x: float,
) -> None:
    """Snap the stack to the right edge, absorbing the local labels it collides with."""
    for lab in stack:
        _snap_x(lab, right_disp_x)

    # A local label that the stack's ideal layout collides with joins the stack,
    # rather than being jumped over (which would read out of line-end order).
    # Repeat, as each join re-lays the stack.  Local labels nothing collides
    # with are left exactly where they are.
    while True:
        ys = _stack_layout(stack)
        joins = [p for p in local if any(_hits_label(lab, y, [p]) for lab, y in zip(stack, ys, strict=True))]
        if not joins:
            break
        for p in joins:
            _snap_x(p, right_disp_x)
        stack.extend(joins)
        ids = {id(p) for p in joins}
        local = [p for p in local if id(p) not in ids]
        placed = [p for p in placed if id(p) not in ids]

    # Separate pile-ups are separate sub-stacks: each clears any remaining
    # (interior) obstacle on its own, so one pile-up never drags another.
    for group, gys in _stack_groups(stack, ys):
        shift = _stack_shift(group, gys, placed)
        for lab, y in zip(group, gys, strict=True):
            lab["yc"] = y + shift
        placed.extend(group)


def _draw_leaders(axes: Axes, labels: list[dict[str, Any]], trans: Transform) -> None:
    """Join each displaced label back to its own line end with a thin leader.

    A label that barely moved gets no leader: the stub would be shorter than the
    text is tall and would read as dirt rather than as a connection.
    """
    inv = trans.inverted()
    for lab in labels:
        if hypot(lab["x0"] - lab["anchor_x0"], lab["yc"] - lab["anchor_yc"]) < lab["h"] * _LEADER_MIN_FRAC:
            continue
        x_anchor = float(trans.transform((lab["x_data"], 0.0))[0])
        x_start, y_start = inv.transform((x_anchor, lab["anchor_yc"]))
        x_end, y_end = inv.transform((lab["x0"] - _GAP_PX, lab["yc"]))
        # add_artist() (not add_line()) so the leader cannot disturb the data
        # limits the labels were just measured against.
        axes.add_artist(
            Line2D(
                [x_start, x_end],
                [y_start, y_end],
                lw=_LEADER_LW,
                color=lab["t"].get_color(),
                alpha=_LEADER_ALPHA,
                zorder=_LEADER_ZORDER,
                clip_on=False,  # snapped stacks can run past ylim
                label="_nolegend_",
            ),
        )


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

    options: AnnotationOptions = stash["options"]
    labels = _build_labels(stash["pairs"], renderer, line_index, (right_x, span, options.near_end))
    if not labels:
        return

    _place_all(labels, line_disps, right_disp_x, force_right=options.force_right)

    # --- write the new positions back in data coordinates
    inv = trans.inverted()
    for lab in labels:
        x_disp = right_disp_x if lab["snapped"] else float(trans.transform((lab["x_data"], 0.0))[0])
        _, y_data = inv.transform((x_disp, lab["yc"]))
        lab["t"].set_y(y_data)
        if lab["snapped"]:
            lab["t"].set_x(right_x)

    if options.leader_lines:
        _draw_leaders(axes, labels, trans)
