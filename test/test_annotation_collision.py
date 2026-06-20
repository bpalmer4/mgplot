"""Test end-of-line annotation collision avoidance.

Run with: uv run python test/test_annotation_collision.py
"""

import tempfile

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd

from mgplot import finalise_plot, line_plot

IDX = pd.period_range("2020-01", periods=36, freq="M")


def _finalise(axes: object, title: str) -> None:
    """Finalise into a throwaway directory (this is what de-collides labels)."""
    with tempfile.TemporaryDirectory() as chart_dir:
        finalise_plot(axes, title=title, chart_dir=chart_dir, dont_close=True)


def test_colliding_end_labels_are_spread() -> None:
    """Lines ending at near-identical values get their labels spread apart."""
    df = pd.DataFrame(
        {
            "alpha": np.linspace(0, 10.0, 36),
            "beta": np.linspace(0, 10.05, 36),
            "gamma": np.linspace(0, 9.95, 36),
            "delta": np.linspace(0, 10.1, 36),
        },
        index=IDX,
    )
    axes = line_plot(df, annotate=True, width=1.0)
    _finalise(axes, "collision test")

    ys = sorted(t.get_position()[1] for t in axes.texts)
    gaps = [b - a for a, b in zip(ys, ys[1:], strict=False)]
    assert len(ys) == 4, f"expected 4 labels, got {len(ys)}"
    assert all(g > 0 for g in gaps), f"labels not separated: gaps={gaps}"
    # all four ended at the rightmost data point, so all snap to one x
    xs = {round(t.get_position()[0], 6) for t in axes.texts}
    assert len(xs) == 1, f"end labels should share one x, got {xs}"
    print("PASS: colliding end labels are spread")


def test_interior_label_stays_at_its_line_end() -> None:
    """A series ending well before the right edge keeps its label at its end."""
    df = pd.DataFrame(
        {
            "ends_early": list(np.linspace(0, 5, 20)) + [np.nan] * 16,
            "full_a": np.linspace(0, 5.0, 36),
            "full_b": np.linspace(0, 5.2, 36),
        },
        index=IDX,
    )
    axes = line_plot(df, annotate=True, width=1.0)
    early_x = axes.texts[0].get_position()[0]  # first drawn label = ends_early
    _finalise(axes, "interior test")

    # the interior label must not have been snapped to the right edge
    right_x = max(line.get_xdata()[-1] for line in axes.get_lines())
    interior_x = axes.texts[0].get_position()[0]
    assert interior_x == early_x, "interior label x should be unchanged"
    assert interior_x < right_x, "interior label should stay left of the right edge"
    print("PASS: interior label stays at its line end")


def test_no_annotation_is_a_noop() -> None:
    """Plots without annotation finalise cleanly (no stash, no movement)."""
    series = pd.Series(np.linspace(0, 5, 36), index=IDX)
    axes = line_plot(series, annotate=False)
    _finalise(axes, "no annotation")
    assert len(axes.texts) == 0, "no annotations expected"
    print("PASS: no-annotation finalise is a no-op")


def test_single_label_unchanged() -> None:
    """A lone annotated line has nothing to collide with and is left in place."""
    series = pd.Series(np.linspace(0, 5, 36), index=IDX)
    axes = line_plot(series, annotate=True)
    y_before = axes.texts[0].get_position()[1]
    _finalise(axes, "single label")
    y_after = axes.texts[0].get_position()[1]
    assert y_before == y_after, f"single label moved: {y_before} -> {y_after}"
    print("PASS: single label unchanged")


if __name__ == "__main__":
    test_colliding_end_labels_are_spread()
    test_interior_label_stays_at_its_line_end()
    test_no_annotation_is_a_noop()
    test_single_label_unchanged()
    print("\nAll annotation collision tests passed!")
