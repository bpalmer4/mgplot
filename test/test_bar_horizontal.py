"""Test horizontal bar plots (bar_plot(horizontal=True)).

Covers:
- single-series horizontal bars with a string index (category labels on y)
- end-of-bar value annotations placed along the x (value) axis
- grouped and stacked multi-column horizontal bars
- stacked bars with negative values (sign-aware bases)
- horizontal=True with a PeriodIndex warns and falls back to vertical
- labels survive finalise_plot()
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg

CATEGORIES = ["NSW", "Vic", "Qld", "SA", "WA"]


def make_series() -> pd.Series:
    """Categorical test series."""
    return pd.Series([5.0, 4.0, 3.0, 2.0, 1.0], index=CATEGORIES, name="test")


def y_labels(ax) -> list[str]:
    """Return the non-empty y tick labels."""
    return [t.get_text() for t in ax.get_yticklabels() if t.get_text()]


def test_horizontal_string_index() -> None:
    """Categories label the y-axis; bar containers hold horizontal bars."""
    ax = mg.bar_plot(make_series(), horizontal=True)
    assert y_labels(ax) == CATEGORIES, f"y labels wrong: {y_labels(ax)}"
    container = ax.containers[0]
    widths = [patch.get_width() for patch in container]
    assert widths == [5.0, 4.0, 3.0, 2.0, 1.0], f"bar widths wrong: {widths}"
    plt.close("all")
    print("PASS: horizontal bars with string index")


def test_horizontal_annotations() -> None:
    """Value annotations sit along the x (value) axis, vertically centred."""
    ax = mg.bar_plot(make_series(), horizontal=True, annotate=True, rounding=0, above=True)
    texts = [t for t in ax.texts if t.get_text()]
    assert len(texts) == len(CATEGORIES), f"expected {len(CATEGORIES)} annotations, got {len(texts)}"
    assert {t.get_text() for t in texts} == {"5", "4", "3", "2", "1"}
    assert all(t.get_va() == "center" for t in texts), "annotations not vertically centred"
    assert all(t.get_ha() == "left" for t in texts), "positive values should be left-aligned"
    plt.close("all")
    print("PASS: horizontal end-of-bar annotations")


def test_horizontal_grouped_and_stacked() -> None:
    """Two-column DataFrames plot grouped or stacked horizontally."""
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [3.0, 2.0, 1.0]}, index=["x", "y", "z"])
    ax = mg.bar_plot(df, horizontal=True)
    assert len(ax.containers) == 2, "grouped: expected two bar containers"
    plt.close("all")

    ax = mg.bar_plot(df, horizontal=True, stacked=True)
    # stacked: second container's bars start where the first ends
    lefts = [patch.get_x() for patch in ax.containers[1]]
    assert lefts == [1.0, 2.0, 3.0], f"stacked bases wrong: {lefts}"
    plt.close("all")
    print("PASS: horizontal grouped and stacked")


def test_horizontal_stacked_negatives() -> None:
    """Negative values stack leftward from zero, positives rightward."""
    df = pd.DataFrame({"a": [2.0, -2.0], "b": [3.0, -3.0]}, index=["up", "down"])
    ax = mg.bar_plot(df, horizontal=True, stacked=True)
    # each b bar starts at the end of its a bar and extends away from zero
    b_spans = [sorted((p.get_x(), p.get_x() + p.get_width())) for p in ax.containers[1]]
    assert b_spans == [[2.0, 5.0], [-5.0, -2.0]], f"sign-aware bases wrong: {b_spans}"
    plt.close("all")
    print("PASS: horizontal stacked with negatives")


def test_periodindex_falls_back_to_vertical() -> None:
    """horizontal=True with a PeriodIndex warns and plots vertical."""
    series = pd.Series(
        [1.0, 2.0, 3.0, 4.0],
        index=pd.period_range("2024Q1", periods=4, freq="Q"),
    )
    ax = mg.bar_plot(series, horizontal=True)
    heights = [patch.get_height() for patch in ax.containers[0]]
    assert heights == [1.0, 2.0, 3.0, 4.0], "PeriodIndex bars should be vertical"
    plt.close("all")
    print("PASS: PeriodIndex falls back to vertical")


def test_per_bar_colors() -> None:
    """A single series with one colour per bar paints each bar individually."""
    import matplotlib.colors as mcolors

    colors = ["deepskyblue", "navy", "#c32148", "gold", "seagreen"]
    for horiz in (True, False):
        ax = mg.bar_plot(make_series(), horizontal=horiz, color=colors, annotate=True)
        got = [mcolors.to_hex(p.get_facecolor()) for p in ax.containers[0]]
        want = [mcolors.to_hex(c) for c in colors]
        assert got == want, f"horizontal={horiz}: per-bar colours wrong: {got}"
        plt.close("all")
    print("PASS: per-bar colours (both orientations)")


def test_labels_survive_finalise() -> None:
    """Category y labels are untouched by finalise_plot's refresh."""
    ax = mg.bar_plot(make_series(), horizontal=True)
    mg.finalise_plot(ax, title="t", dont_save=True, dont_close=True)
    assert y_labels(ax) == CATEGORIES, f"y labels lost in finalise: {y_labels(ax)}"
    plt.close("all")
    print("PASS: category labels survive finalise")


if __name__ == "__main__":
    test_horizontal_string_index()
    test_horizontal_annotations()
    test_horizontal_grouped_and_stacked()
    test_horizontal_stacked_negatives()
    test_periodindex_falls_back_to_vertical()
    test_per_bar_colors()
    test_labels_survive_finalise()
    print("\nAll horizontal bar tests passed!")
