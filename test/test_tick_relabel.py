"""Test that tick-label options survive the refresh in finalise_plot().

Covers:
- tick_relabel: per-plot callable applied to generated tick labels
- max_ticks: honoured by the final refresh in finalise_plot()
- label_rotation: survives finalise for PeriodIndex bar plots
- finalise_plot() closes its own figure, not pyplot's current figure
"""

import re

import matplotlib

matplotlib.use("Agg")
import matplotlib._pylab_helpers as ph
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def two_digit(label: str) -> str:
    """Shorten 4-digit years to 2 digits."""
    return re.sub(r"\b(?:19|20)(\d{2})\b", r"\1", label)


def make_series() -> pd.Series:
    """Quarterly test series spanning 16 years."""
    idx = pd.period_range("2010Q1", "2025Q4", freq="Q")
    return pd.Series(range(len(idx)), index=idx, name="test")


def test_tick_relabel_survives_finalise() -> None:
    """tick_relabel and max_ticks must survive finalise_plot's refresh."""
    series = make_series()
    ax = mg.line_plot(series, tick_relabel=two_digit, max_ticks=6)
    mg.finalise_plot(ax, title="t1", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels, "no tick labels generated"
    assert all(not YEAR_RE.search(label) for label in labels), f"4-digit year leaked: {labels}"
    assert len(labels) <= 6, f"max_ticks=6 not honoured after finalise: {labels}"
    plt.close("all")
    print("PASS: tick_relabel + max_ticks survive finalise")


def test_bar_label_rotation_survives_finalise() -> None:
    """label_rotation on PeriodIndex bar plots must survive finalise_plot."""
    series = make_series()[-12:]
    ax = mg.bar_plot(series, label_rotation=45)
    mg.finalise_plot(ax, title="t2", dont_save=True, dont_close=True)
    rotations = {t.get_rotation() for t in ax.get_xticklabels()}
    assert rotations == {45.0}, f"label_rotation lost in finalise: {rotations}"
    plt.close("all")
    print("PASS: bar label_rotation survives finalise")


def test_default_labels_unchanged() -> None:
    """Without tick_relabel, the contextual 4-digit labels are unchanged."""
    series = make_series()
    ax = mg.line_plot(series)
    mg.finalise_plot(ax, title="t3", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert any(YEAR_RE.search(label) for label in labels), f"default labels broken: {labels}"
    plt.close("all")
    print("PASS: default labels unchanged")


def test_finalise_closes_own_figure() -> None:
    """finalise_plot must close the finalised figure, not pyplot's current one."""
    plt.close("all")
    fig_a, ax_a = plt.subplots()  # the chart being finalised
    ax_a.plot([1, 2, 3])
    fig_b, _ax_b = plt.subplots()  # innocent bystander = plt.gcf()
    assert plt.gcf() is fig_b
    mg.finalise_plot(ax_a, title="t4", dont_save=True)
    open_figs = {m.canvas.figure for m in ph.Gcf.get_all_fig_managers()}
    assert fig_a not in open_figs, "finalised figure was not closed"
    assert fig_b in open_figs, "wrong figure closed by finalise_plot"
    plt.close("all")
    print("PASS: finalise closes its own figure")


if __name__ == "__main__":
    test_tick_relabel_survives_finalise()
    test_bar_label_rotation_survives_finalise()
    test_default_labels_unchanged()
    test_finalise_closes_own_figure()
    print("\nAll tick relabel tests passed!")
