"""Test scatter_plot() and scatter_plot_finalise().

Run with: uv run python test/test_scatter_plot.py
"""

import contextlib
import io
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D

from mgplot import multi_start, scatter_plot, scatter_plot_finalise, set_chart_dir

mpl.use("Agg")

DIAGONAL_LABEL = "45° (equal)"


def _points(ax: Axes, i: int = 0) -> PathCollection:
    """Return the i-th scatter collection on the axes."""
    collection = ax.collections[i]
    assert isinstance(collection, PathCollection), f"Expected PathCollection, got {type(collection)}"
    return collection


def _line(ax: Axes, label: str | None = None) -> Line2D:
    """Return the only line on the axes, or the line with the given label."""
    lines = [ln for ln in ax.get_lines() if label is None or ln.get_label() == label]
    assert len(lines) == 1, f"Expected one line (label={label}), got {len(lines)}"
    return lines[0]


def _xy(line: Line2D) -> tuple[np.ndarray, np.ndarray]:
    """Return a line's data as float arrays."""
    return np.asarray(line.get_xdata(), dtype=float), np.asarray(line.get_ydata(), dtype=float)


def _raises(error: type[Exception], func: Callable[[], object]) -> str:
    """Assert func raises error; return the message."""
    try:
        func()
    except error as e:
        return str(e)
    raise AssertionError(f"Expected {error.__name__}")


def _stdout(func: Callable[[], object]) -> str:
    """Run func and return what it printed."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        func()
    return buffer.getvalue()


def test_data_validation() -> None:
    """Anything other than a two-column numeric DataFrame is rejected."""
    good = pd.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]})
    series: Any = good["x"]  # deliberately the wrong type
    _raises(TypeError, lambda: scatter_plot(series))
    msg = _raises(ValueError, lambda: scatter_plot(good[["x"]]))
    assert "got 1" in msg, msg
    msg = _raises(ValueError, lambda: scatter_plot(good.assign(z=[5.0, 6.0])))
    assert "got 3" in msg, msg
    msg = _raises(ValueError, lambda: scatter_plot(pd.DataFrame({"x": [1.0, 2.0], "y": ["a", "b"]})))
    assert "y" in msg, msg
    plt.close("all")
    print("PASS: data validation")


def test_dropna() -> None:
    """A NaN in either column drops that row; dropna=False keeps them."""
    df = pd.DataFrame({"x": [1.0, 2.0, np.nan, 4.0, 5.0], "y": [10.0, np.nan, 30.0, 40.0, 50.0]})
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax)
    offsets = np.asarray(_points(ax).get_offsets())
    assert len(offsets) == 3, f"Expected 3 points after dropna, got {len(offsets)}"
    assert list(offsets[:, 0]) == [1.0, 4.0, 5.0], f"Wrong rows kept: {offsets[:, 0]}"

    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, dropna=False)
    count = len(np.asarray(_points(ax).get_offsets()))
    assert count == 5, f"dropna=False should pass all rows to matplotlib, got {count}"
    plt.close("all")
    print("PASS: dropna")


def test_empty_after_dropna() -> None:
    """No complete rows -> the line_plot-style warning and nothing drawn."""
    df = pd.DataFrame({"x": [1.0, np.nan], "y": [np.nan, 2.0]})
    _, ax = plt.subplots()
    out = _stdout(lambda: scatter_plot(df, ax=ax))
    assert "No data to plot in scatter_plot()" in out, out
    assert len(ax.collections) == 0, "Nothing should be drawn"
    plt.close("all")
    print("PASS: empty after dropna")


def test_default_style() -> None:
    """Default colour comes from the mgplot palette, not a hard-coded name."""
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax)
    expected = mcolors.to_rgba("blue", alpha=0.6)  # get_color_list(1)[0], DEFAULT_ALPHA
    got = np.asarray(_points(ax).get_facecolor())[0]
    assert np.allclose(got, expected), f"Expected {expected}, got {got}"
    plt.close("all")
    print("PASS: default style")


def test_diagonal() -> None:
    """The diagonal satisfies y == x and spans the data on both axes, not just x."""
    df = pd.DataFrame({"x": [0.0, 1.0, 2.0], "y": [5.0, 10.0, 7.0]})
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, diagonal=True)
    x, y = _xy(_line(ax, DIAGONAL_LABEL))
    assert np.array_equal(x, y), f"Diagonal points are not y == x: {x}, {y}"
    assert x.min() == 0.0, f"Diagonal should start at 0, got {x.min()}"
    assert x.max() == 10.0, f"Diagonal should reach the y maximum 10, got {x.max()}"

    # a dict is merged over the house style
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, diagonal={"color": "green"})
    line = _line(ax, DIAGONAL_LABEL)
    assert line.get_color() == "green", line.get_color()
    assert line.get_linestyle() == "--", "House style should survive a partial dict"

    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, diagonal=False)
    assert len(ax.get_lines()) == 0, "diagonal=False should draw nothing"
    plt.close("all")
    print("PASS: diagonal")


def test_fit() -> None:
    """Data built as y = 2x + 1 gives a drawn line with slope 2 and intercept 1."""
    x_data = [3.0, -1.0, 7.0, 0.5, 4.0]  # deliberately unsorted
    df = pd.DataFrame({"x": x_data, "y": [2 * v + 1 for v in x_data]})
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, fit=True, color="purple")
    x, y = _xy(_line(ax))
    slope = (y[1] - y[0]) / (x[1] - x[0])
    intercept = y[0] - slope * x[0]
    assert np.isclose(slope, 2.0), f"Expected slope 2, got {slope}"
    assert np.isclose(intercept, 1.0), f"Expected intercept 1, got {intercept}"
    assert sorted(x) == [-1.0, 7.0], f"Fit should span the x-range of the points, got {x}"
    assert _line(ax).get_color() == "purple", "Fit should default to the points' colour"
    plt.close("all")
    print("PASS: fit")


def test_highlight_latest() -> None:
    """The highlighted point is the latest index value, not the last row nor the max x."""
    index = pd.PeriodIndex(["2021Q2", "2021Q4", "2021Q1", "2021Q3"], freq="Q")
    df = pd.DataFrame({"x": [9.0, 2.0, 5.0, 3.0], "y": [90.0, 20.0, 50.0, 30.0]}, index=index)
    # last row is 2021Q3 (3, 30); max x is 2021Q2 (9, 90); latest is 2021Q4 (2, 20)
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, highlight_latest=True)
    assert len(ax.collections) == 2, f"Expected points + highlight, got {len(ax.collections)}"
    star = _points(ax, 1)
    assert np.array_equal(np.asarray(star.get_offsets()), [[2.0, 20.0]]), star.get_offsets()
    assert star.get_label() == "Latest (2021Q4)", star.get_label()
    plt.close("all")
    print("PASS: highlight_latest")


def test_report_corr() -> None:
    """The correlation is computed from the data and appended to the label."""
    negative = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [8.0, 6.0, 4.0, 2.0]})
    _, ax = plt.subplots()
    scatter_plot(negative, ax=ax, report_corr=True)
    assert _points(ax).get_label() == "r = -1.00", _points(ax).get_label()

    half = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 3.0, 2.0]})  # r = 0.5 exactly
    _, ax = plt.subplots()
    scatter_plot(half, ax=ax, label="GDP", report_corr=True)
    assert _points(ax).get_label() == "GDP (r = 0.50)", _points(ax).get_label()
    plt.close("all")
    print("PASS: report_corr")


def test_ax_chaining() -> None:
    """Two calls on one axes give two point collections, each with its own fit line."""
    era1 = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})
    era2 = pd.DataFrame({"x": [4.0, 5.0, 6.0], "y": [8.0, 10.0, 12.0]})
    _, ax = plt.subplots()
    ax = scatter_plot(era1, ax=ax, color="red", fit=True)
    ax = scatter_plot(era2, ax=ax, color="green", fit=True)
    assert len(ax.collections) == 2, f"Expected 2 collections, got {len(ax.collections)}"
    assert len(ax.get_lines()) == 2, f"Expected 2 fit lines, got {len(ax.get_lines())}"
    assert [ln.get_color() for ln in ax.get_lines()] == ["red", "green"]
    plt.close("all")
    print("PASS: ax chaining")


def test_plot_from() -> None:
    """plot_from trims a PeriodIndex; on another index it warns and plots everything."""
    index = pd.period_range("2020Q1", periods=6, freq="Q")
    df = pd.DataFrame({"x": range(6), "y": range(6)}, index=index, dtype=float)
    _, ax = plt.subplots()
    scatter_plot(df, ax=ax, plot_from=pd.Period("2020Q4", freq="Q"))
    offsets = np.asarray(_points(ax).get_offsets())
    assert list(offsets[:, 0]) == [3.0, 4.0, 5.0], f"plot_from not applied: {offsets[:, 0]}"

    _, ax = plt.subplots()
    out = _stdout(lambda: scatter_plot(df, ax=ax, plot_from=None))
    assert out == "", f"plot_from=None should be silent: {out}"
    assert len(np.asarray(_points(ax).get_offsets())) == 6

    labelled = df.set_axis([f"p{i}" for i in range(6)])
    _, ax = plt.subplots()
    out = _stdout(lambda: scatter_plot(labelled, ax=ax, plot_from=2))
    assert "plot_from ignored" in out, out
    assert len(np.asarray(_points(ax).get_offsets())) == 6
    plt.close("all")
    print("PASS: plot_from")


def test_finalise() -> None:
    """scatter_plot_finalise() saves a chart and reports unknown kwargs."""
    df = pd.DataFrame(
        {"x": [1.0, 2.0, 3.0, 4.0], "y": [1.5, 1.9, 3.2, 3.9]},
        index=pd.period_range("2024Q1", periods=4, freq="Q"),
    )
    with tempfile.TemporaryDirectory() as tmp:
        set_chart_dir(tmp)
        out = _stdout(
            lambda: scatter_plot_finalise(
                df,
                title="Scatter test",
                lfooter="Australia.",
                rfooter="Source: test",
                diagonal=True,
                report_corr=True,
                highlight_latest=True,
            )
        )
        assert "Unexpected keyword" not in out, out
        assert len(list(Path(tmp).glob("*.png"))) == 1, "Chart was not saved"

        unknown: dict[str, Any] = {"title": "Unknown kwarg", "bogus": 1}
        out = _stdout(lambda: scatter_plot_finalise(df, **unknown))
        assert "Unexpected keyword argument 'bogus' received by scatter_plot_finalise()" in out, out

        # multi_start passes plot_from through to scatter_plot
        out = _stdout(lambda: multi_start(df, function=scatter_plot_finalise, starts=[None, -2], title="MS"))
        assert "Unexpected keyword" not in out, out
        assert "Warning" not in out, out
        set_chart_dir(".")
    plt.close("all")
    print("PASS: scatter_plot_finalise")


if __name__ == "__main__":
    test_data_validation()
    test_dropna()
    test_empty_after_dropna()
    test_default_style()
    test_diagonal()
    test_fit()
    test_highlight_latest()
    test_report_corr()
    test_ax_chaining()
    test_plot_from()
    test_finalise()
    print("\nAll scatter_plot tests passed!")
