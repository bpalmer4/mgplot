"""Test annotated vertical lines: axvline dicts carrying a text label.

Run with: uv run python test/test_axvline_text.py
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.font_manager import FontProperties
from matplotlib.text import Annotation

from mgplot import bar_plot, line_plot
from mgplot.finalise_plot import VLINE_TEXT_FONTSIZE, VLINE_TEXT_OFFSET, finalise_plot

IDX = pd.period_range("2020-01", periods=24, freq="M")


def _label(axes: Axes, text: str) -> Annotation:
    """Return the single annotation carrying the given text.

    Note Annotation.get_position() is the offset, not the anchor -- the
    blended-transform anchor this feature cares about is .xy.
    """
    found = [t for t in axes.texts if isinstance(t, Annotation) and t.get_text() == text]
    assert len(found) == 1, f"Expected exactly 1 {text!r} annotation, found {len(found)}"
    return found[0]


def test_text_is_drawn_and_rotated() -> None:
    """A text key should add a rotated annotation, defaulting to xx-small."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "color": "red", "text": "COVID"},
        dont_save=True,
        dont_close=True,
    )

    label = _label(axes, "COVID")
    assert label.get_rotation() == 90, f"Expected rotation 90, got {label.get_rotation()}"
    expected_size = FontProperties(size=VLINE_TEXT_FONTSIZE).get_size_in_points()
    assert label.get_fontsize() == expected_size, f"Expected xx-small, got {label.get_fontsize()}"
    assert label.get_color() == "red", f"Expected label to inherit line colour, got {label.get_color()}"
    assert label.get_horizontalalignment() == "left", "Expected label to sit right of the line"

    plt.close()
    print("PASS: axvline text drawn, rotated, colour inherited")


def test_text_keys_do_not_reach_matplotlib() -> None:
    """text/loc/text_kwargs must be popped before ax.axvline() is called."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[6], "text": "GFC", "loc": "top", "text_kwargs": {"fontweight": "bold"}},
        dont_save=True,
        dont_close=True,
    )

    vlines = [
        ln
        for ln in axes.get_lines()
        if np.asarray(ln.get_ydata()).size == 2 and np.asarray(ln.get_xdata())[0] == IDX[6].ordinal
    ]
    assert len(vlines) == 1, f"Expected 1 vline at {IDX[6]}, found {len(vlines)}"
    assert _label(axes, "GFC").get_fontweight() == "bold", "text_kwargs should override defaults"

    plt.close()
    print("PASS: label keys popped before matplotlib sees them")


def test_auto_picks_top_when_data_is_low() -> None:
    """Data hugging the bottom of the axes should push the label to the top."""
    series = pd.Series(np.full(24, 1.0), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "text": "high"},
        ylim=(0.0, 100.0),
        dont_save=True,
        dont_close=True,
    )

    _, y = _label(axes, "high").xy
    assert y > 0.5, f"Expected label near the top (y>0.5 in axes coords), got {y}"
    valign = _label(axes, "high").get_verticalalignment()
    assert valign == "top", f"Expected va='top' so the text hangs downward, got {valign}"

    plt.close()
    print("PASS: auto picks top when data sits low")


def test_auto_picks_bottom_when_data_is_high() -> None:
    """Data hugging the top of the axes should push the label to the bottom."""
    series = pd.Series(np.full(24, 99.0), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "text": "low"},
        ylim=(0.0, 100.0),
        dont_save=True,
        dont_close=True,
    )

    _, y = _label(axes, "low").xy
    assert y < 0.5, f"Expected label near the bottom (y<0.5 in axes coords), got {y}"
    valign = _label(axes, "low").get_verticalalignment()
    assert valign == "bottom", f"Expected va='bottom' so the text rises upward, got {valign}"

    plt.close()
    print("PASS: auto picks bottom when data sits high")


def test_auto_is_local_not_whole_chart() -> None:
    """Placement should follow the data near the line, not the whole series."""
    # Rises steeply: low at the left-hand line, high at the right-hand one.
    series = pd.Series(np.linspace(0.0, 100.0, 24), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline=[{"x": IDX[2], "text": "early"}, {"x": IDX[21], "text": "late"}],
        dont_save=True,
        dont_close=True,
    )

    early_y = _label(axes, "early").xy[1]
    late_y = _label(axes, "late").xy[1]
    assert early_y > 0.5, f"Expected 'early' at the top over low data, got y={early_y}"
    assert late_y < 0.5, f"Expected 'late' at the bottom under high data, got y={late_y}"

    plt.close()
    print("PASS: auto placement is local to each line")


def test_explicit_loc_overrides_auto() -> None:
    """An explicit loc should win over what auto would have chosen."""
    series = pd.Series(np.full(24, 1.0), index=IDX)  # low data => auto would say top
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "text": "forced", "loc": "bottom"},
        ylim=(0.0, 100.0),
        dont_save=True,
        dont_close=True,
    )

    _, y = _label(axes, "forced").xy
    assert y < 0.5, f"Expected forced label at the bottom, got y={y}"

    plt.close()
    print("PASS: explicit loc overrides auto")


def test_side_word_flips_label_to_the_left() -> None:
    """A 'left' side word should flip the label to the left flank of the line.

    Uses 'top left' so both knobs are exercised at once: 'top' must still set
    va='top', while 'left' must set ha='right' and a negative x-offset. The
    default (right) placement would give ha='left' and a positive offset, so
    this cannot pass down the unchanged path.
    """
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "text": "flip", "loc": "top left"},
        dont_save=True,
        dont_close=True,
    )

    label = _label(axes, "flip")
    valign, halign = label.get_verticalalignment(), label.get_horizontalalignment()
    assert valign == "top", f"Expected va='top' from 'top', got {valign}"
    assert halign == "right", f"Expected ha='right' from 'left', got {halign}"
    x_off, _ = label.get_position()  # get_position() is the offset, not the anchor
    assert x_off == -VLINE_TEXT_OFFSET, f"Expected x-offset {-VLINE_TEXT_OFFSET} to the left, got {x_off}"

    plt.close()
    print("PASS: 'left' side word flips the label to the left flank")


def test_several_labelled_lines() -> None:
    """A sequence of labelled lines should produce a label per line."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    wanted = ["one", "two", "three", "four", "five"]
    finalise_plot(
        axes,
        axvline=[{"x": x, "text": t} for x, t in zip(IDX[2:22:4], wanted, strict=True)],
        dont_save=True,
        dont_close=True,
    )

    drawn = {t.get_text() for t in axes.texts}
    assert set(wanted) <= drawn, f"Expected all of {wanted}, got {drawn}"

    plt.close()
    print("PASS: five labelled lines all drawn")


def test_period_x_with_text() -> None:
    """A Period x should still convert to an ordinal when a label is attached."""
    period = pd.Period("2020-05", freq="M")
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    finalise_plot(axes, axvline={"x": period, "text": "May"}, dont_save=True, dont_close=True)

    x, _ = _label(axes, "May").xy
    assert x == period.ordinal, f"Expected label anchored at ordinal {period.ordinal}, got {x}"

    plt.close()
    print("PASS: Period x converts with a label attached")


def test_unlabelled_vline_unchanged() -> None:
    """An axvline without text should add no annotation at all."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    before = len(axes.texts)
    finalise_plot(axes, axvline={"x": IDX[12], "color": "red"}, dont_save=True, dont_close=True)

    assert len(axes.texts) == before, "A plain axvline should not add text"

    plt.close()
    print("PASS: unlabelled axvline unchanged")


def test_bad_loc_raises() -> None:
    """An unrecognised loc is a typo, and should raise."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    try:
        finalise_plot(axes, axvline={"x": IDX[12], "text": "x", "loc": "middle"}, dont_save=True)
    except ValueError as e:
        assert "loc" in str(e), f"Expected a message naming loc, got: {e}"
        plt.close()
        print("PASS: bad loc raises")
        return
    plt.close()
    raise AssertionError("Expected ValueError for loc='middle'")


def test_loc_without_text_raises() -> None:
    """Label options without any text to place should raise."""
    series = pd.Series(np.linspace(0.0, 10.0, 24), index=IDX)
    axes = line_plot(series)
    try:
        finalise_plot(axes, axvline={"x": IDX[12], "loc": "top"}, dont_save=True)
    except ValueError as e:
        assert "text" in str(e), f"Expected a message naming text, got: {e}"
        plt.close()
        print("PASS: loc without text raises")
        return
    plt.close()
    raise AssertionError("Expected ValueError for loc without text")


def test_bar_plot_is_measurable() -> None:
    """Bars live in ax.patches, not get_lines(); auto should read them.

    Bars run from the zero baseline to their top, so negative bars leave the
    room underneath them. The answer is therefore 'bottom' -- and the no-data
    fallback is 'top', so this fails rather than passing by coincidence.
    """
    series = pd.Series(np.full(24, -99.0), index=IDX)
    axes = bar_plot(series)
    finalise_plot(
        axes,
        axvline={"x": IDX[12], "text": "bars"},
        ylim=(-100.0, 0.0),
        dont_save=True,
        dont_close=True,
    )

    _, y = _label(axes, "bars").xy
    assert y < 0.5, f"Expected label below the hanging bars, got y={y}"

    plt.close()
    print("PASS: bar plot patches are measured")


if __name__ == "__main__":
    test_text_is_drawn_and_rotated()
    test_text_keys_do_not_reach_matplotlib()
    test_auto_picks_top_when_data_is_low()
    test_auto_picks_bottom_when_data_is_high()
    test_auto_is_local_not_whole_chart()
    test_explicit_loc_overrides_auto()
    test_side_word_flips_label_to_the_left()
    test_several_labelled_lines()
    test_period_x_with_text()
    test_unlabelled_vline_unchanged()
    test_bad_loc_raises()
    test_loc_without_text_raises()
    test_bar_plot_is_measurable()
    print("\nAll annotated axvline tests passed!")
