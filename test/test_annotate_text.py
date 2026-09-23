"""Test string labels for the end-of-line annotation.

Run with: uv run python test/test_annotate_text.py
"""

import contextlib
import io
import tempfile
from itertools import pairwise

import matplotlib as mpl

mpl.use("Agg")

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

from mgplot import finalise_plot, line_plot

IDX = pd.period_range("2020-01", periods=36, freq="M")


def _finalise(axes: Axes, title: str) -> None:
    """Finalise into a throwaway directory (this is what de-collides labels)."""
    with tempfile.TemporaryDirectory() as chart_dir:
        finalise_plot(axes, title=title, chart_dir=chart_dir, dont_close=True)


def _frame(**ends: float) -> pd.DataFrame:
    """Build a frame whose columns rise linearly to the given end values."""
    return pd.DataFrame({k: np.linspace(0, v, 36) for k, v in ends.items()}, index=IDX)


def test_scalar_string_broadcasts() -> None:
    """A single string labels every series, and rounding does not touch it."""
    df = _frame(alpha=1.0, beta=5.0, gamma=9.0)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        axes = line_plot(df, annotate="26Q2", rounding=3)
    texts = [t.get_text() for t in axes.texts]
    assert texts == ["  26Q2"] * 3, f"expected three broadcast labels, got {texts}"
    # a widened LineKwargs means validate_kwargs() has nothing to complain about
    assert "annotate" not in stdout.getvalue(), f"unexpected kwarg warning: {stdout.getvalue()!r}"
    print("PASS: scalar string broadcasts to every series")


def test_per_series_list() -> None:
    """A list of strings labels each series in turn."""
    df = _frame(alpha=1.0, beta=5.0, gamma=9.0)
    axes = line_plot(df, annotate=["26Q2", "26Q3", "26Q4"])
    texts = [t.get_text() for t in axes.texts]
    assert texts == ["  26Q2", "  26Q3", "  26Q4"], f"per-series labels wrong: {texts}"
    print("PASS: per-series list labels each series")


def test_mixed_list_skips_falsey_entries() -> None:
    """False and the empty string still mean "no label" in a per-series list."""
    df = _frame(alpha=1.0, beta=5.0, gamma=9.0)
    axes = line_plot(df, annotate=["26Q2", False, ""])
    texts = [t.get_text() for t in axes.texts]
    assert texts == ["  26Q2"], f"only the first series should be labelled, got {texts}"
    print("PASS: falsey entries in a list are skipped")


def test_string_labels_de_collide() -> None:
    """String labels on near-identical line ends are spread apart, as values are."""
    df = _frame(alpha=10.0, beta=10.05, gamma=9.95, delta=10.1)
    axes = line_plot(df, annotate=["26Q1", "26Q2", "26Q3", "26Q4"], width=1.0)
    before = sorted(t.get_position()[1] for t in axes.texts)
    _finalise(axes, "string label collision")

    ys = sorted(t.get_position()[1] for t in axes.texts)
    gaps = [b - a for a, b in pairwise(ys)]
    assert len(ys) == 4, f"expected 4 labels, got {len(ys)}"
    assert all(g > 0 for g in gaps), f"labels not separated: gaps={gaps}"
    assert ys != before, "labels should have been moved apart"
    print("PASS: string labels de-collide")


def test_string_labels_honour_force_right() -> None:
    """force_right snaps string labels to the rightmost data point too."""
    df = pd.DataFrame(
        {
            "ends_early": list(np.linspace(0, 5, 20)) + [np.nan] * 16,
            "full_a": np.linspace(0, 5.0, 36),
        },
        index=IDX,
    )
    axes = line_plot(df, annotate="26Q2", width=1.0, force_right=True)
    _finalise(axes, "string label force right")

    right_x = max(float(np.asarray(line.get_xdata(), dtype=float)[-1]) for line in axes.get_lines())
    xs = {round(t.get_position()[0], 6) for t in axes.texts}
    assert xs == {round(float(right_x), 6)}, f"labels not all at the right edge: {xs}"
    assert all(t.get_text() == "  26Q2" for t in axes.texts), "label text should survive the snap"
    print("PASS: string labels honour force_right")


def test_string_labels_get_leader_lines() -> None:
    """A displaced string label is joined back to its line end by a leader."""
    df = _frame(alpha=10.0, beta=10.05, gamma=9.95)
    axes = line_plot(df, annotate=["26Q1", "26Q2", "26Q3"], width=1.0, leader_lines=True)
    _finalise(axes, "string label leaders")
    leaders = [ln for ln in axes.lines if ln.get_label() == "_nolegend_"]
    assert leaders, "colliding string labels should have leaders"
    assert len(leaders) <= len(axes.texts), "more leaders than labels"
    print("PASS: string labels get leader lines")


def test_annotate_true_is_unchanged() -> None:
    """annotate=True still prints the end-point value, and rounding still bites."""
    series = pd.Series(np.linspace(0, 5.125, 36), index=IDX)
    axes = line_plot(series, annotate=True, rounding=2)
    assert [t.get_text() for t in axes.texts] == ["  5.12"], f"got {[t.get_text() for t in axes.texts]}"

    axes = line_plot(series, annotate=True, rounding=0)
    assert [t.get_text() for t in axes.texts] == ["  5"], f"got {[t.get_text() for t in axes.texts]}"
    print("PASS: annotate=True is unchanged")


def test_string_label_needs_a_real_endpoint() -> None:
    """An all-NaN series gets no label, even when text is supplied."""
    df = pd.DataFrame(
        {"good": np.linspace(0, 5, 36), "empty": [np.nan] * 36},
        index=IDX,
    )
    axes = line_plot(df, annotate="26Q2")
    texts = [t.get_text() for t in axes.texts]
    assert texts == ["  26Q2"], f"only the series with data should be labelled, got {texts}"
    print("PASS: a string label still needs a real endpoint")


if __name__ == "__main__":
    test_scalar_string_broadcasts()
    test_per_series_list()
    test_mixed_list_skips_falsey_entries()
    test_string_labels_de_collide()
    test_string_labels_honour_force_right()
    test_string_labels_get_leader_lines()
    test_annotate_true_is_unchanged()
    test_string_label_needs_a_real_endpoint()
    print("\nAll annotate-text tests passed!")
