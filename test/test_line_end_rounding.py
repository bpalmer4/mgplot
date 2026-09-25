"""Test that end-of-line value labels round, rather than truncate.

With rounding=0 the label used to be int(y), which truncates toward zero, so
19.77 read "19". Each rounding=0 case below has a fractional part above .5,
so truncation and rounding disagree and only correct rounding can pass.

Run with: uv run python test/test_line_end_rounding.py
"""

import matplotlib as mpl

mpl.use("Agg")

import numpy as np
import pandas as pd

from mgplot import line_plot

IDX = pd.period_range("2020-01", periods=36, freq="M")


def _end_label(end: float, rounding: int) -> str:
    """Plot a series ending at `end` and return the label line_plot adds."""
    series = pd.Series(np.linspace(0, end, 36), index=IDX)
    axes = line_plot(series, annotate=True, rounding=rounding)
    texts = [t.get_text() for t in axes.texts]
    assert len(texts) == 1, f"expected one end-of-line label, got {texts}"
    return texts[0]


def test_rounding_zero_rounds_up() -> None:
    """Positive values with a fraction above .5 round up, not down."""
    for end, expected in ((19.77, "  20"), (30.92, "  31")):
        label = _end_label(end, rounding=0)
        assert label == expected, f"{end} with rounding=0: expected {expected!r}, got {label!r}"
    print("PASS: rounding=0 rounds positive values to nearest")


def test_rounding_zero_negative() -> None:
    """Negative values round away from zero when that is nearest, not toward it."""
    label = _end_label(-19.7, rounding=0)
    assert label == "  -20", f"-19.7 with rounding=0: expected '  -20', got {label!r}"
    print("PASS: rounding=0 rounds negative values to nearest")


def test_rounding_one_unchanged() -> None:
    """Regression: positive rounding still prints the given number of places."""
    label = _end_label(19.77, rounding=1)
    assert label == "  19.8", f"19.77 with rounding=1: expected '  19.8', got {label!r}"
    print("PASS: rounding=1 is unchanged")


if __name__ == "__main__":
    test_rounding_zero_rounds_up()
    test_rounding_zero_negative()
    test_rounding_one_unchanged()
    print("\nAll line-end rounding tests passed!")
