"""Test that keyword checking accepts an int where a float is expected, as Python typing does.

Covers:
- check() accepts int for float, but not bool (a subclass of int)
- check() still rejects float for int
- ylim=(0, 1.1) passes finalise_plot's keyword check without a mismatch warning
"""

import contextlib
import io

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg
from mgplot.keyword_checking import check


def test_int_accepted_for_float() -> None:
    """An int satisfies a float annotation (PEP 484 numeric tower)."""
    assert check(0, float)
    assert check(3, float | None)
    assert check((0, 1.1), tuple[float, float])
    print("PASS: int accepted for float")


def test_bool_still_rejected_for_float() -> None:
    """A bool is an int subclass, but not a number in this sense."""
    flag = True
    assert not check(flag, float)
    print("PASS: bool rejected for float")


def test_float_still_rejected_for_int() -> None:
    """The widening runs one way only: a float does not satisfy int."""
    assert not check(1.5, int)
    print("PASS: float rejected for int")


def test_ylim_with_int_has_no_mismatch_warning() -> None:
    """ylim=(0, 1.1) must not print a 'Mismatched type' warning."""
    series = pd.Series([0.5, 0.8, 0.6], index=pd.period_range("2024Q1", periods=3, freq="Q"))
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        mg.line_plot_finalise(series, title="t", ylim=(0, 1.1), dont_save=True)
    assert "Mismatched type" not in printed.getvalue(), printed.getvalue()
    plt.close("all")
    print("PASS: ylim=(0, 1.1) accepted")


if __name__ == "__main__":
    test_int_accepted_for_float()
    test_bool_still_rejected_for_float()
    test_float_still_rejected_for_int()
    test_ylim_with_int_has_no_mismatch_warning()
    print("\nAll int-for-float tests passed!")
