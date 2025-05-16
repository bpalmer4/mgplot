"""
date_utils.py
This module contains functions to work with date-like 
(i.e. not time-like) PeriodIndex frequencies in Pandas.
"""

import calendar
from enum import Enum
from pandas import Period, PeriodIndex, period_range

class DateLike(Enum):
    """Recognised date-like PeriodIndex frequencies"""
    YEARS = 1
    QUARTERS = 2
    MONTHS = 3
    DAYS = 4
    BAD = 5

frequencies = {
    #freq: [Periods from smaller to larger]
    "D": [DateLike.DAYS, DateLike.MONTHS, DateLike.YEARS],
    "M": [DateLike.MONTHS, DateLike.YEARS],
    "Q": [DateLike.QUARTERS, DateLike.YEARS],
    "Y": [DateLike.YEARS]
}

r_freqs = {v[0]: k for k, v in frequencies.items()}

intervals = {
    DateLike.YEARS:   [1, 2, 4, 5,
                    10, 20, 40, 50,
                    100, 200, 400, 500,
                    1_000, 2_000, 4_000, 5_000,
                    10_000, 20_000, 40_000, 50_000],
    DateLike.QUARTERS:    [1, 2],
    DateLike.MONTHS:  [1, 2, 3, 4, 6],
    DateLike.DAYS:    [1, 2, 4, 7, 14],
}


def get_count(
    p: PeriodIndex,
    max_ticks: int
) -> tuple[int, DateLike, int]:
    """
    Work out the label frequency and interval for a date-like 
    PeriodIndex. 

    Parameters
    - p: PeriodIndex - the PeriodIndex
    - max_ticks -  the maximum number of ticks [suggestive]

    Returns a tuple:
    - the total number of ticks: int
    - the type of ticks to highlight: str
    - the tick interval: int
    """

    # --- sanity checks
    if max_ticks < 5:
        max_ticks = 5
    error = (0, DateLike.BAD, 0)
    if p.empty:
        return error
    freq: str = p.freqstr[0].upper()
    if freq not in frequencies:
        print("Unrecognised date-like PeriodIndex frequency {freq}")
        return error

	# --- calculate
    for test_freq in frequencies[freq]:
        r_freq = r_freqs[test_freq]
        for interval in intervals[test_freq]:
            count = (
                p.max().asfreq(r_freq, how='end').ordinal
                - p.min().asfreq(r_freq, how='end').ordinal
                + 1
            ) // interval
            if count <= max_ticks:
                return count, test_freq, interval


def day_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """ to do"""

    def add_month(label: str, month: str) -> str:
        return f"{label}\n{month}"

    def add_year(label: str, year: str) -> str:
        label = label.replace("\n", " ") if len(label) > 2 else f"{label} {month}"
        label = f"{label}\n{year}"
        return label

    if not labels:
        return labels

    start = min(labels.keys())
    month_previous: str = calendar.month_abbr[start.month]
    year_previous: str = str(start.year)
    final_year = True

    for period in sorted(labels.keys()):
        label = str(period.day)
        month = calendar.month_abbr[period.month]
        year = str(period.year)

        if month_previous != month:
            label = add_month(label, month)

        if year_previous != year:
            final_year = False
            label = add_year(label, year)

        labels[period] = label

    if final_year:
        final_period = max(labels.keys())
        labels[final_period] = add_year(label, year)

    return labels


def month_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """ to do """

    subset = (
        PeriodIndex([c for c in p if c.day == 1]) if p.freqstr[0] == "D"
        else p
    )

    start = 0
    if interval > 1:
        mod_months = [(c.month - 1) % interval for c in subset]
        start = 0 if 0 not in mod_months else mod_months.index(0)
    return { k: "" for k in subset[start::interval] }


def month_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """ to do """

    if not labels:
        return labels

    start = min(labels.keys())
    year_previous: str = str(start.year)
    final_year = True

    for period in sorted(labels.keys()):
        label = calendar.month_abbr[period.month]
        year = str(period.year)

        if year_previous != year or period.month == 1:
            label = f"{label}\n{year}"
            year_previous = year
            final_year = False

        labels[period] = label

    if final_year:
        final_period = max(labels.keys())
        label = labels[final_period]
        year = str(final_period.year)
        label = f"{label}\n{year}"
        labels[final_period] = label

    return labels


def qtr_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """ to do """

    start = 0
    if interval > 1:
        mod_qtrs = [(c.quarter - 1) % interval for c in p]
        start = 0 if 0 not in mod_qtrs else mod_qtrs.index(0)
    return {k: "" for k in p[start::interval]}


def qtr_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """ to do """

    if not labels:
        return labels

    final_year = True
    for period in sorted(labels.keys()):
        quarter = period.quarter
        label = f"Q{quarter}"
        if quarter == 1:
            final_year = False
            label = f"{label}\n{period.year}"
        labels[period] = label

    if final_year:
        final_period = max(labels.keys())
        label = labels[final_period]
        year = str(final_period.year)
        label = f"{label}\n{year}"
        labels[final_period] = label

    return labels


def year_locator(p: PeriodIndex, interval: int) -> dict[Period, str]:
    """ to do """

    subset = (
        PeriodIndex([c for c in p if c.month == 1 and c.day == 1])
        if p.freqstr[0] == "D"
        else PeriodIndex([c for c in p if c.month == 1 ])
        if p.freqstr[0] == "M"
        else PeriodIndex([c for c in p if c.quarter == 1 ])
        if p.freqstr[0] == "Q"
        else p
    )

    start = 0
    if interval > 1:
        mod_years = [(c.year - 1) % interval for c in p]
        start = 0 if 0 not in mod_years else mod_years.index(0)
    return {k: "" for k in subset[start::interval]}


def year_labeller(labels: dict[Period, str]) -> dict[Period, str]:
    """ to do """

    if not labels:
        return labels

    for period in sorted(labels.keys()):
        label = str(period.year)
        labels[period] = label
    return labels


def enlabel(
    p: PeriodIndex,
    max_ticks: int
) -> dict[Period, str]:
    """
    Provide a dictionary of labels for the date-like PeriodIndex.

    Parameters
    - p: PeriodIndex - the PeriodIndex
    - max_ticks -  the maximum number of ticks [suggestive]

    Returns a dictionary:
    - keys are the Periods to label
    - values are the labels to apply
    """

    labels = {}
    count, date_like, interval = get_count(p, max_ticks)
    if date_like == DateLike.BAD:
        return labels

    target_freq = r_freqs[date_like]
    complete = period_range(start=p.min(), end=p.max(), freq=p.freqstr)

    if target_freq == "D":
        start = 0 if interval == 2 and count % 2 else interval // 2
        labels = {k: "" for k in complete[start::interval]}
        labels = day_labeller(labels)
        return labels

    if target_freq == "M":
        labels = month_locator(complete, interval)
        labels = month_labeller(labels)
        return labels

    if target_freq == "Q":
        labels = qtr_locator(complete, interval)
        labels = qtr_labeller(labels)
        return labels

    if target_freq == "Y":
        labels = year_locator(complete, interval)
        labels = year_labeller(labels)
        return labels

    return labels


# --- test ---
if __name__ == "__main__":

    # test 1
    pi = PeriodIndex(
        ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"], freq="d"
    )
    print(enlabel(pi, 10), "\n")

    # test 2
    pi = period_range(
        start="2020-01-01", end="2020-01-15", freq="D"
    )
    print(enlabel(pi, 10), "\n")

    # test 3
    pi = period_range(
        start="2020-02-01", end="2022-07-15", freq="D"
    )
    print(enlabel(pi, 10), "\n")

    # test 4
    pi = period_range(
        start="2020-Q2", end="2022-Q4", freq="Q"
    )
    print(enlabel(pi, 10), "\n")

    # test 6
    pi = period_range(
        start="1950-01-01", end="2026-12-15", freq="D"
    )
    print(enlabel(pi, 10))
