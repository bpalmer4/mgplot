"""Test x-axis ticks and labels for intraday (minute and hour) PeriodIndex data.

Covers:
- 5-minute bars over two trading days: hour ticks at round times, after finalise's refresh
- a refreshed 5-minute range that starts off the hour still gets ticks on the hour
- hourly bars over six weeks: day ticks at midnight, labelled as days
- the first label carries the year; later hour labels carry the date only at a new day

Run with: uv run python test/test_intraday_ticks.py
"""

import re

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg
from mgplot.axis_utils import make_ilabels

TIME_RE = re.compile(r"^\d{2}:\d{2}")


def trading_days(freq: str, days: list[str]) -> pd.Series:
    """Bars from 09:30 to 16:00 on each day: the overnight gaps are left out, as in market data."""
    index = pd.PeriodIndex(
        [p for day in days for p in pd.period_range(f"{day} 09:30", f"{day} 15:55", freq=freq)],
    )
    return pd.Series(range(len(index)), index=index, name="price", dtype=float)


def tick_periods(ax: plt.Axes, freq: str) -> list[pd.Period]:
    """Read the axis ticks back as Periods of the plotted frequency."""
    return [pd.Period(ordinal=int(t), freq=freq) for t in ax.get_xticks()]


def test_five_minute_two_days() -> None:
    """Two days of 5-minute bars: ticks on round hours, labelled with times, after finalise."""
    series = trading_days("5min", ["2026-11-19", "2026-11-20"])
    ax = mg.line_plot(series)
    mg.finalise_plot(ax, title="intraday 5min", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    periods = tick_periods(ax, "5min")
    assert labels, "no tick labels generated"
    assert all(TIME_RE.match(label) for label in labels), f"labels are not times: {labels}"
    assert all(p.minute == 0 for p in periods), f"ticks off the hour: {periods}"
    assert "2026" in labels[0], f"first label lacks the year: {labels[0]!r}"
    plt.close("all")
    print("PASS: 5-minute bars over two days")


def test_unaligned_range_ticks_on_the_hour() -> None:
    """A 5-minute range starting at 09:31 (as rebuilt from axis limits) still ticks on the hour."""
    p = pd.period_range("2026-11-19 09:31", "2026-11-19 15:56", freq="5min")
    ticks, labels = make_ilabels(p, 10)
    periods = [pd.Period(ordinal=t, freq="5min") for t in ticks]
    assert ticks, "no ticks for an unaligned range"
    assert all(per.minute == 0 for per in periods), f"ticks off the hour: {labels}"
    print("PASS: unaligned 5-minute range ticks on the hour")


def test_hourly_six_weeks() -> None:
    """Six weeks of hourly bars: ticks at midnight, labelled as days, not times."""
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-10-12", "2026-11-20")]
    series = trading_days("h", days)
    ax = mg.line_plot(series)
    mg.finalise_plot(ax, title="intraday hourly", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    periods = tick_periods(ax, "h")
    assert labels, "no tick labels generated"
    assert all((p.hour, p.minute) == (0, 0) for p in periods), f"day ticks not at midnight: {periods}"
    assert not any(":" in label for label in labels), f"day ticks labelled as times: {labels}"
    plt.close("all")
    print("PASS: hourly bars over six weeks")


def test_date_only_at_new_day() -> None:
    """Hour labels carry the date at a new day only; the year only on the first label."""
    p = pd.period_range("2026-12-31 18:00", "2027-01-01 06:00", freq="h")
    ticks, labels = make_ilabels(p, 6)
    assert ticks, "no ticks generated"
    assert "2026" in labels[0], f"first label lacks the year: {labels[0]!r}"
    new_day = [label for label in labels if "1 Jan" in label]
    assert new_day, f"no label marks the new day: {labels}"
    assert "2027" in new_day[0], f"new year not marked: {new_day[0]!r}"
    assert sum("\n" in label for label in labels) == 2, f"date on more than the day changes: {labels}"
    print("PASS: date only at a new day")


if __name__ == "__main__":
    test_five_minute_two_days()
    test_unaligned_range_ticks_on_the_hour()
    test_hourly_six_weeks()
    test_date_only_at_new_day()
    print("\nAll intraday tick tests passed!")
