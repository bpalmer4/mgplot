"""Test ohlc_plot(): candles on bar positions, session boundaries, bar ticks and overlays.

Covers:
- bar i is drawn at x = i: closed hours, weekends and holidays take no space
- a boundary line wherever the next bar starts later than this bar ends: overnight and
  weekends for hourly bars, a mid-session data gap for minute bars, weekends for daily bars;
  none on a chart with more than max_boundaries of them (two years of daily bars)
- tick labels from the bars: day ticks on the session edges for a week of hourly bars, hour
  ticks for a single day of minute bars, month ticks for half a year of daily bars; a
  session's last tick never crowds the next session's first
- a moving average of the closes and volume bars land on their bars; data with periods that
  are not bars, another frequency, no PeriodIndex, a plot that cannot place its data on bars,
  and a second chart are refused
- share_bars() makes a panel on the same bars and boundaries, with dates on the bottom only
- a Period axvline lands on its bar; one that is not a bar is refused
- a candle that closes at the low of the chart keeps the y-margin below it
- no x-gridlines, so every vertical line is a session boundary; the y-gridlines stay

Run with: uv run python test/test_ohlc_plot.py
"""

import itertools

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import mgplot as mg

HOURS = ("09:00", "15:00")  # seven hourly bars a day
WEEK = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20", "2026-11-23"]


def candles(index: pd.PeriodIndex) -> pd.DataFrame:
    """Alternately rising and falling bars on a gently rising path."""
    opens = [100.0 + i * 0.1 for i in range(len(index))]
    closes = [o + (1.0 if i % 2 == 0 else -1.0) for i, o in enumerate(opens)]
    return pd.DataFrame(
        {
            "Open": opens,
            "High": [max(o, c) + 0.5 for o, c in zip(opens, closes, strict=True)],
            "Low": [min(o, c) - 0.5 for o, c in zip(opens, closes, strict=True)],
            "Close": closes,
            "Volume": 1000,
        },
        index=index,
    )


def hourly_week() -> pd.DataFrame:
    """Seven hourly bars on each of six trading days, Monday to the next Monday."""
    index = pd.PeriodIndex(
        [p for day in WEEK for p in pd.period_range(f"{day} {HOURS[0]}", f"{day} {HOURS[1]}", freq="h")],
    )
    return candles(index)


def boundaries(ax: plt.Axes) -> list[float]:
    """Return the x-positions of the session-boundary lines."""
    return sorted(float(line.get_xdata()[0]) for line in ax.get_lines() if line.get_color() == "lightgrey")


def test_bars_and_boundaries_hourly_week() -> None:
    """A week of hourly bars: candles at 0..n-1, one boundary between each pair of sessions."""
    data = hourly_week()
    ax = mg.ohlc_plot(data)
    bodies = [patch.get_x() + patch.get_width() / 2 for patch in ax.patches]
    assert bodies == [float(i) for i in range(len(data))], "candle bodies are not at bar positions"
    expected = [7 * day - 0.5 for day in range(1, len(WEEK))]
    assert boundaries(ax) == expected, f"boundaries {boundaries(ax)}, expected {expected}"
    mg.finalise_plot(ax, title="ohlc week", dont_save=True, dont_close=True)
    ticks = list(ax.get_xticks())
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert ticks == [-0.5, *expected], f"day ticks not on the session edges: {ticks}"
    assert not any(":" in label for label in labels), f"day ticks labelled as times: {labels}"
    plt.close("all")
    print("PASS: hourly week: bar positions, boundaries and day ticks")


def test_minute_gap_and_hour_ticks() -> None:
    """One day of 2-minute bars with an 18-minute hole: one boundary there, hour ticks."""
    index = pd.period_range("2026-11-23 10:00", "2026-11-23 16:00", freq="2min")
    hole = (index.start_time > pd.Timestamp("2026-11-23 10:56")) & (
        index.start_time < pd.Timestamp("2026-11-23 11:14")
    )
    data = candles(index[~hole])
    ax = mg.ohlc_plot(data)
    first_after = int((data.index.start_time >= pd.Timestamp("2026-11-23 11:14")).argmax())
    assert boundaries(ax) == [first_after - 0.5], f"gap boundary {boundaries(ax)}"
    mg.finalise_plot(ax, title="ohlc gap", dont_save=True, dont_close=True)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels, "no tick labels generated"
    assert all(label[:2].isdigit() and label[2:5] == ":00" for label in labels), labels
    assert not any(label.startswith("11:00") for label in labels), "a tick for a bar in the gap"
    plt.close("all")
    print("PASS: minute bars: data-gap boundary and hour ticks")


def test_no_crowded_ticks_across_sessions() -> None:
    """Three ASX-like sessions of 2-minute bars: no tick crowds the next across a close."""
    days = ["2026-11-20", "2026-11-23", "2026-11-24"]
    data = candles(
        pd.PeriodIndex(
            [p for day in days for p in pd.period_range(f"{day} 10:00", f"{day} 16:10", freq="2min")],
        ),
    )
    ax = mg.ohlc_plot(data)
    mg.finalise_plot(ax, title="ohlc sessions", dont_save=True, dont_close=True)
    ticks = list(ax.get_xticks())
    labels = [t.get_text() for t in ax.get_xticklabels()]
    spacings = sorted(b - a for a, b in itertools.pairwise(ticks))
    median = spacings[len(spacings) // 2]
    assert spacings[0] >= median / 2, f"crowded ticks: {list(zip(ticks, labels, strict=True))}"
    dated = [label for label in labels if "\n" in label]
    assert len(dated) == len(days), f"each session's first tick should carry its date: {labels}"
    plt.close("all")
    print("PASS: no crowded ticks across sessions")


def test_daily_weekends_and_month_ticks() -> None:
    """Half a year of weekday bars: a boundary at each weekend, month ticks."""
    data = candles(pd.PeriodIndex(pd.bdate_range("2026-05-25", "2026-11-24"), freq="D"))
    ax = mg.ohlc_plot(data)
    mondays = [i - 0.5 for i in range(1, len(data)) if data.index[i].day_of_week == 0]
    assert boundaries(ax) == mondays, "weekend boundaries are not before each Monday"
    mg.finalise_plot(ax, title="ohlc daily", dont_save=True, dont_close=True)
    labels = [t.get_text().split("\n")[0] for t in ax.get_xticklabels()]
    assert labels[:3] == ["Jun", "Jul", "Aug"], f"month ticks expected: {labels}"
    plt.close("all")
    print("PASS: daily bars: weekend boundaries and month ticks")


def test_no_boundaries_on_long_daily() -> None:
    """Two years of weekday bars (about 104 weekends): no lines; a higher max_boundaries draws them."""
    data = candles(pd.PeriodIndex(pd.bdate_range("2024-11-25", "2026-11-24"), freq="D"))
    weekends = sum(1 for i in range(1, len(data)) if data.index[i].day_of_week == 0)
    ax = mg.ohlc_plot(data)
    assert boundaries(ax) == [], f"{len(boundaries(ax))} boundary lines on a two-year daily chart"
    plt.close("all")
    ax = mg.ohlc_plot(data, max_boundaries=weekends)
    assert len(boundaries(ax)) == weekends, "max_boundaries did not bring the weekend lines back"
    plt.close("all")
    print("PASS: no boundaries on a two-year daily chart")


def test_moving_average_overlay() -> None:
    """A rolling mean of the closes is drawn on its bars, with its values."""
    data = hourly_week()
    ma = data["Close"].rolling(7).mean()
    ax = mg.ohlc_plot(data)
    mg.line_plot(ma, ax=ax, annotate=False)
    line = ax.get_lines()[-1]
    assert list(line.get_xdata()) == list(range(6, len(data))), "MA not on its bars"
    assert list(line.get_ydata()) == list(ma.dropna()), "MA values changed"
    mg.fill_between_plot(pd.DataFrame({"lo": ma - 1, "hi": ma + 1}).dropna(), ax=ax)
    plt.close("all")
    print("PASS: moving average and band land on their bars")


def test_refusals() -> None:
    """Data off the bars, another frequency, unplaceable plots and a second chart all raise."""
    data = hourly_week()
    attempts = {
        "periods not bars": lambda ax: mg.line_plot(
            pd.Series(1.0, index=pd.period_range("2026-11-21 10:00", periods=3, freq="h")),
            ax=ax,
        ),
        "daily on hourly": lambda ax: mg.line_plot(
            pd.Series(1.0, index=pd.period_range("2026-11-16", periods=5, freq="D")),
            ax=ax,
        ),
        "bar_plot off the bars": lambda ax: mg.bar_plot(
            pd.Series(1.0, index=pd.period_range("2026-11-21 10:00", periods=3, freq="h")),
            ax=ax,
        ),
        "plain index": lambda ax: mg.line_plot(pd.Series([1.0, 2.0, 3.0]), ax=ax),
        "run_plot": lambda ax: mg.run_plot(data["Close"], ax=ax),
        "second ohlc": lambda ax: mg.ohlc_plot(data, ax=ax),
        "off-bar axvline": lambda ax: mg.finalise_plot(
            ax,
            title="x",
            axvline={"x": pd.Period("2026-11-21 10:00", freq="h")},
            dont_save=True,
        ),
    }
    for name, attempt in attempts.items():
        ax = mg.ohlc_plot(data)
        try:
            attempt(ax)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{name} was not refused")
        plt.close("all")
    line_axes = mg.line_plot(data["Close"])
    try:
        mg.ohlc_plot(data, ax=line_axes)
    except ValueError:
        pass
    else:
        raise AssertionError("ohlc_plot on an axes holding a line chart was not refused")
    plt.close("all")
    print("PASS: refusals")


def test_bar_plot_on_bars() -> None:
    """bar_plot() on an OHLC chart puts each bar on its candle's position."""
    data = hourly_week()
    ax = mg.ohlc_plot(data)
    candle_bodies = len(ax.patches)
    mg.bar_plot(data["Volume"], ax=ax, annotate=False)
    volume = ax.patches[candle_bodies:]
    xs = [patch.get_x() + patch.get_width() / 2 for patch in volume]
    assert xs == [float(i) for i in range(len(data))], "volume bars not on their candles"
    plt.close("all")
    print("PASS: bar_plot on the bars")


def test_share_bars_panel() -> None:
    """A panel under the candles: same bars and boundaries, dates on the bottom panel only."""
    data = hourly_week()
    ma = data["Close"].rolling(7).mean()
    _fig, (top, bottom) = plt.subplots(2, 1, sharex=True)
    mg.ohlc_plot(data, ax=top)
    mg.finalise_plot(top, title="candles", axes_only=True)
    mg.share_bars(bottom, top)
    mg.line_plot(ma, ax=bottom, annotate=False)
    assert list(bottom.get_lines()[-1].get_xdata()) == list(range(6, len(data))), "MA not on its bars"
    assert boundaries(bottom) == boundaries(top), "panel boundaries differ from the candles'"
    mg.finalise_plot(bottom, filename="panel", dont_save=True, dont_close=True)
    top_labels = [t.get_text() for t in top.get_xticklabels() if t.get_visible() and t.get_text()]
    bottom_labels = [t.get_text() for t in bottom.get_xticklabels() if t.get_visible() and t.get_text()]
    assert not top_labels, f"dates shown on the candle panel: {top_labels}"
    assert bottom_labels, "no dates on the bottom panel"
    plt.close("all")
    _fig, (left, right) = plt.subplots(1, 2)
    try:
        mg.share_bars(right, left)
    except ValueError:
        pass
    else:
        raise AssertionError("share_bars accepted an axes without an OHLC chart")
    plt.close("all")
    print("PASS: share_bars panel")


def test_period_axvline_on_its_bar() -> None:
    """A Period axvline lands on the position of its bar."""
    data = hourly_week()
    ax = mg.ohlc_plot(data, boundaries=False)
    when = pd.Period("2026-11-18 12:00", freq="h")
    mg.finalise_plot(ax, title="x", axvline={"x": when, "color": "black"}, dont_save=True, dont_close=True)
    xs = [float(line.get_xdata()[0]) for line in ax.get_lines()]
    assert xs == [float(data.index.get_loc(when))], f"axvline at {xs}"
    plt.close("all")
    print("PASS: Period axvline on its bar")


def test_margin_below_a_low_close() -> None:
    """A candle closing at the chart's low still leaves the y-margin below it."""
    data = hourly_week()
    low = data["Low"].min() - 5.0
    data.iloc[3, data.columns.get_loc("Low")] = low
    data.iloc[3, data.columns.get_loc("Close")] = low  # a body whose base is the chart's low
    ax = mg.ohlc_plot(data)
    mg.finalise_plot(ax, title="x", dont_save=True, dont_close=True)
    assert ax.get_ylim()[0] < low, f"no margin below the low: ylim {ax.get_ylim()}, low {low}"
    plt.close("all")
    print("PASS: margin below a low close")


def test_no_x_gridlines() -> None:
    """After finalise, an OHLC chart has no visible x-gridlines but keeps its y-gridlines."""
    ax = mg.ohlc_plot(hourly_week())
    mg.finalise_plot(ax, title="x", dont_save=True, dont_close=True)
    assert ax.get_xticks().size, "no x ticks to carry gridlines"
    assert not any(line.get_visible() for line in ax.xaxis.get_gridlines()), "x-gridlines drawn"
    assert any(line.get_visible() for line in ax.yaxis.get_gridlines()), "y-gridlines lost"
    plt.close("all")
    print("PASS: no x-gridlines, y-gridlines kept")


def test_missing_column() -> None:
    """A frame without a Close column is refused."""
    try:
        mg.ohlc_plot(hourly_week().drop(columns="Close"))
    except ValueError:
        pass
    else:
        raise AssertionError("missing Close column was not refused")
    plt.close("all")
    print("PASS: missing column refused")


if __name__ == "__main__":
    test_bars_and_boundaries_hourly_week()
    test_minute_gap_and_hour_ticks()
    test_no_crowded_ticks_across_sessions()
    test_daily_weekends_and_month_ticks()
    test_no_boundaries_on_long_daily()
    test_moving_average_overlay()
    test_refusals()
    test_bar_plot_on_bars()
    test_share_bars_panel()
    test_period_axvline_on_its_bar()
    test_margin_below_a_low_close()
    test_no_x_gridlines()
    test_missing_column()
    print("All ohlc_plot tests passed!")
