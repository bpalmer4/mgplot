"""Test x-axis ticks and labels for weekly PeriodIndex data.

Covers:
- two years of weeks: month ticks on the first week starting in each month, after finalise
- six months of weeks: week ticks labelled by the week's start day, not its last day
- fifteen years of weeks: year ticks on the first week starting in each year
- a weekly series with missing weeks still gets ticks across the whole span

Run with: uv run python test/test_weekly_ticks.py
"""

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg
from mgplot.axis_utils import make_ilabels

FIRST_WEEK_DAYS = 7  # a week starting on day 1-7 of a month is that month's first week
YEAR_DIGITS = 4
MIN_SPAN_TICKS = 6  # a two-year span should get at least this many ticks


def weekly(start: str, periods: int) -> pd.Series:
    """Make a weekly series (weeks Monday to Sunday)."""
    index = pd.period_range(start, periods=periods, freq="W")
    return pd.Series(range(periods), index=index, name="price", dtype=float)


def tick_weeks(ticks: list[int]) -> list[pd.Period]:
    """Read tick ordinals back as weekly Periods."""
    return [pd.Period(ordinal=int(t), freq="W") for t in ticks]


def test_two_years_month_ticks() -> None:
    """Two years of weeks: ticks on the first week starting in a month, after finalise."""
    ax = mg.line_plot(weekly("2024-11-18", 105))
    mg.finalise_plot(ax, title="weekly 2y", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    weeks = tick_weeks(list(ax.get_xticks()))
    assert labels, "no tick labels generated"
    assert all(w.start_time.day <= FIRST_WEEK_DAYS for w in weeks), f"not first weeks: {weeks}"
    assert any(label in ("Mar", "May", "Jul") for label in labels), f"no month labels: {labels}"
    assert "2026" in labels, f"year change not labelled: {labels}"
    plt.close("all")
    print("PASS: two years of weeks, month ticks")


def test_six_months_week_ticks_by_start_day() -> None:
    """Six months of weeks: week ticks labelled by start day (16, not 22, for 16-22 Nov)."""
    p = pd.period_range("2026-06-01", "2026-11-16", freq="W")
    ticks, labels = make_ilabels(p, 13)
    weeks = tick_weeks(ticks)
    assert ticks, "no ticks generated"
    for week, label in zip(weeks, labels, strict=True):
        day = label.split("\n")[0].split(" ")[0]
        assert day == str(week.start_time.day), f"{week} labelled {label!r}, not by its start day"
    assert any("\n" in label for label in labels), f"no month marked under a day: {labels}"
    print("PASS: six months of weeks, labelled by start day")


def test_fifteen_years_year_ticks() -> None:
    """Fifteen years of weeks: ticks on the first week starting in a year, labelled as years."""
    p = pd.period_range("2011-01-03", "2025-12-29", freq="W")
    ticks, labels = make_ilabels(p, 13)
    weeks = tick_weeks(ticks)
    assert ticks, "no ticks generated"
    assert all(w.start_time.month == 1 and w.start_time.day <= FIRST_WEEK_DAYS for w in weeks), weeks
    assert all(label.isdigit() and len(label) == YEAR_DIGITS for label in labels), f"not years: {labels}"
    print("PASS: fifteen years of weeks, year ticks")


def test_missing_weeks_still_ticked() -> None:
    """Missing weeks (an incomplete index) still get ticks across the whole span."""
    series = weekly("2024-11-18", 105).iloc[::3]
    ax = mg.line_plot(series)
    mg.finalise_plot(ax, title="weekly gaps", dont_save=True, dont_close=True)
    weeks = tick_weeks(list(ax.get_xticks()))
    assert len(weeks) >= MIN_SPAN_TICKS, f"too few ticks: {weeks}"
    assert weeks[-1] > series.index[len(series) // 2], "ticks stop part-way through the data"
    plt.close("all")
    print("PASS: missing weeks still ticked")


if __name__ == "__main__":
    test_two_years_month_ticks()
    test_six_months_week_ticks_by_start_day()
    test_fifteen_years_year_ticks()
    test_missing_weeks_still_ticked()
    print("\nAll weekly tick tests passed!")
