"""Test that axhline, axvline, axhspan, axvspan accept single dicts and sequences.

Run with: uv run python test/test_splat_sequences.py
"""

import matplotlib.pyplot as plt
import pandas as pd

from mgplot import line_plot
from mgplot.finalise_plot import finalise_plot


def _make_series() -> pd.Series:
    return pd.Series(range(1, 11), index=pd.period_range("2020-01", periods=10, freq="M"))


def test_axhline_single_dict() -> None:
    """A single dict should draw one horizontal line."""
    ax = line_plot(_make_series())
    finalise_plot(ax, axhline={"y": 5, "color": "red"}, dont_save=True, dont_close=True)

    hlines = [l for l in ax.get_lines() if len(l.get_xdata()) == 2 and l.get_ydata()[0] == 5]
    assert len(hlines) == 1, f"Expected 1 hline at y=5, found {len(hlines)}"

    plt.close()
    print("PASS: axhline single dict")


def test_axhline_sequence() -> None:
    """A sequence of dicts should draw multiple horizontal lines."""
    ax = line_plot(_make_series())
    finalise_plot(
        ax,
        axhline=[{"y": 3, "color": "red"}, {"y": 7, "color": "blue"}],
        dont_save=True,
        dont_close=True,
    )

    ys = {l.get_ydata()[0] for l in ax.get_lines() if len(l.get_xdata()) == 2}
    assert 3 in ys, "Expected hline at y=3"
    assert 7 in ys, "Expected hline at y=7"

    plt.close()
    print("PASS: axhline sequence")


def test_axvline_sequence() -> None:
    """A sequence of dicts should draw multiple vertical lines."""
    ax = line_plot(_make_series())
    finalise_plot(
        ax,
        axvline=[{"x": 2, "color": "red"}, {"x": 8, "color": "blue"}],
        dont_save=True,
        dont_close=True,
    )

    xs = {l.get_xdata()[0] for l in ax.get_lines() if len(l.get_ydata()) == 2}
    assert 2 in xs, "Expected vline at x=2"
    assert 8 in xs, "Expected vline at x=8"

    plt.close()
    print("PASS: axvline sequence")


def test_axhspan_single_dict() -> None:
    """A single dict should draw one horizontal span."""
    ax = line_plot(_make_series())
    n_patches_before = len(ax.patches)
    finalise_plot(ax, axhspan={"ymin": 2, "ymax": 4, "alpha": 0.3}, dont_save=True, dont_close=True)

    assert len(ax.patches) == n_patches_before + 1, "Expected 1 new patch from axhspan"

    plt.close()
    print("PASS: axhspan single dict")


def test_axhspan_sequence() -> None:
    """A sequence of dicts should draw multiple horizontal spans."""
    ax = line_plot(_make_series())
    n_patches_before = len(ax.patches)
    finalise_plot(
        ax,
        axhspan=[{"ymin": 1, "ymax": 3, "alpha": 0.2}, {"ymin": 6, "ymax": 8, "alpha": 0.2}],
        dont_save=True,
        dont_close=True,
    )

    assert len(ax.patches) == n_patches_before + 2, "Expected 2 new patches from axhspan sequence"

    plt.close()
    print("PASS: axhspan sequence")


def test_axvspan_sequence() -> None:
    """A sequence of dicts should draw multiple vertical spans."""
    ax = line_plot(_make_series())
    n_patches_before = len(ax.patches)
    finalise_plot(
        ax,
        axvspan=[{"xmin": 1, "xmax": 3}, {"xmin": 6, "xmax": 8}],
        dont_save=True,
        dont_close=True,
    )

    assert len(ax.patches) == n_patches_before + 2, "Expected 2 new patches from axvspan sequence"

    plt.close()
    print("PASS: axvspan sequence")


def test_axvline_period() -> None:
    """A Period passed as axvline x should be converted to its ordinal."""
    period = pd.Period("2020-05", freq="M")
    ax = line_plot(_make_series())
    finalise_plot(
        ax,
        axvline={"x": period, "color": "red"},
        dont_save=True,
        dont_close=True,
    )

    xs = {l.get_xdata()[0] for l in ax.get_lines() if len(l.get_ydata()) == 2}
    assert period.ordinal in xs, f"Expected vline at x={period.ordinal}, got {xs}"

    plt.close()
    print("PASS: axvline with Period")


def test_axvline_period_freq_mismatch() -> None:
    """A Period with a different freq than the axes should raise."""
    ax = line_plot(_make_series())  # monthly data
    wrong = pd.Period("2020Q1", freq="Q")
    try:
        finalise_plot(ax, axvline={"x": wrong}, dont_save=True, dont_close=True)
    except ValueError as e:
        assert "freq" in str(e).lower(), f"Expected freq-mismatch message, got: {e}"
        plt.close()
        print("PASS: axvline Period freq mismatch raises")
        return
    plt.close()
    raise AssertionError("Expected ValueError for mismatched Period freq")


def test_plot_freq_mismatch() -> None:
    """Plotting two series with different freqs on the same axes should raise."""
    monthly = _make_series()
    quarterly = pd.Series(range(1, 5), index=pd.period_range("2020Q1", periods=4, freq="Q"))
    ax = line_plot(monthly)
    try:
        line_plot(quarterly, ax=ax)
    except ValueError as e:
        assert "freq" in str(e).lower(), f"Expected freq-mismatch message, got: {e}"
        plt.close()
        print("PASS: mixed-freq plots on one axes raises")
        return
    plt.close()
    raise AssertionError("Expected ValueError for mixed freqs on one axes")


if __name__ == "__main__":
    test_axhline_single_dict()
    test_axhline_sequence()
    test_axvline_sequence()
    test_axhspan_single_dict()
    test_axhspan_sequence()
    test_axvspan_sequence()
    test_axvline_period()
    test_axvline_period_freq_mismatch()
    test_plot_freq_mismatch()
    print("\nAll splat sequence tests passed!")
