"""Test that an annual PeriodIndex bar chart does not gain a labelled year before its first bar.

A bar chart's left x-limit sits half a bar before the first bar, so truncating it to an
integer ordinal named the previous year; set_xticks then widened the axis to show that tick,
leaving an empty slot and a stray label (e.g. "2020" before a 2021-2025 chart).
"""

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg

FIRST, LAST = "2021", "2025"


def make_series() -> pd.Series:
    """Annual test series, 2021-2025."""
    idx = pd.period_range(FIRST, LAST, freq="Y")
    return pd.Series([110.0, 128.0, 119.0, 118.0, 121.0], index=idx, name="test")


def test_no_year_before_first_bar() -> None:
    """No tick label or axis space for the year before the first bar."""
    ax = mg.bar_plot(make_series())
    mg.finalise_plot(ax, title="t", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    assert "2020" not in labels, f"stray year before the first bar: {labels}"
    first_ordinal = pd.Period(FIRST, freq="Y").ordinal
    assert ax.get_xlim()[0] > first_ordinal - 1, f"axis widened to the previous year: {ax.get_xlim()}"
    plt.close("all")
    print("PASS: no year before the first bar")


def test_no_year_after_last_bar() -> None:
    """No tick label for the year after the last bar."""
    ax = mg.bar_plot(make_series())
    mg.finalise_plot(ax, title="t", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    assert "2026" not in labels, f"stray year after the last bar: {labels}"
    plt.close("all")
    print("PASS: no year after the last bar")


if __name__ == "__main__":
    test_no_year_before_first_bar()
    test_no_year_after_last_bar()
    print("\nAll annual bar tick tests passed!")
