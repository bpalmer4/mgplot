mgplot
======

Description
-----------
mgplot is an open-source Python frontend for matplotlib designed for
time-series chart creation with PeriodIndex data. It simplifies common
economic and financial plots while:

1. producing time-series charts that can be tricky to create directly,
2. finalising (or publishing) charts with titles, labels, annotations, etc.,
3. minimising code duplication, and maintaining a consistent style.

Installation
------------
```bash
pip install mgplot
```

Or using uv:
```bash
uv add mgplot
```

Requirements: Python 3.10+, pandas, matplotlib, numpy

Import
------
```python
import mgplot as mg
```

Quick Example
-------------
```python
import pandas as pd
import mgplot as mg

# Create sample data with PeriodIndex
data = pd.Series(
    [100, 102, 105, 103, 108],
    index=pd.period_range("2024Q1", periods=5, freq="Q")
)

# Plot and finalise in one step
mg.line_plot_finalise(data, title="Quarterly Data", ylabel="Value")
```

Plot Functions
--------------
All plot functions take a pandas Series or DataFrame with a PeriodIndex
as the first argument and return a matplotlib Axes object. Keyword
arguments control styling and behavior:

- `bar_plot()` -- vertical bar plot (grouped or stacked) with intelligent
  PeriodIndex labeling
- `fill_between_plot()` -- shaded region between two bounds (requires
  2-column DataFrame)
- `growth_plot()` -- plots annual and periodic growth rates (requires
  2-column DataFrame with pre-calculated growth)
- `line_plot()` -- one or more lines with optional annotations
- `postcovid_plot()` -- data as a line with pre-COVID linear projection
- `revision_plot()` -- designed to plot ABS-style data revisions
- `run_plot()` -- line plot with background highlighting for monotonic
  increasing/decreasing runs
- `seastrend_plot()` -- seasonal and trend components on one plot
- `series_growth_plot()` -- calculates and plots annual (line) and
  periodic (bars) growth from a single Series
- `summary_plot()` -- latest data point against historical range with
  z-score visualization

Finalising Plots
----------------
Once a plot is generated, finalise it with titles, labels, and save to file:

```python
ax = mg.line_plot(data)
mg.finalise_plot(ax, title="My Chart", ylabel="Units", tag="my_chart")
```

Axis Tick Labels
----------------
For PeriodIndex data, x-axis tick labels are generated contextually:
the tick density is chosen to fit within `max_ticks`, and labels show
the period with years marked at transitions (e.g. a monthly axis shows
`Feb Mar ... 2024 ... Feb`, a quarterly axis shows `Q2 Q3 2025 Q2`).

Three keyword arguments control the labels on the period-indexed plot
functions (`line_plot`, `bar_plot`, `growth_plot`, `fill_between_plot`,
`run_plot`, and their `*_finalise` variants):

- `max_ticks` -- the maximum number of ticks (suggestive, not exact).
  The global default is `mg.get_setting("max_ticks")`.
- `tick_relabel` -- a callable applied to each generated label string,
  after the contextual labelling has run. Use it to restyle labels
  without losing the transition logic.
- `label_rotation` -- (`bar_plot` only) rotates the x-axis tick labels.

For example, to convert 4-digit year labels to 2-digit years:

```python
import re

def two_digit_years(label: str) -> str:
    """Shorten 4-digit years to 2 digits (e.g. 2024 -> 24)."""
    return re.sub(r"\b(?:19|20)(\d{2})\b", r"\1", label)

# default labels:           2010  2012  2014  ...  2024  2026
# with tick_relabel:          10    12    14  ...    24    26
mg.line_plot_finalise(data, title="My Chart", tick_relabel=two_digit_years)
```

Because `tick_relabel` operates on the label strings, this works
unchanged on quarterly or monthly axes too: a label such as `2024`
marking a year transition becomes `24`, while the `Q2`/`Mar` labels
between transitions pass through untouched.

These options are stashed on the matplotlib Axes when the plot is drawn,
and `finalise_plot()` honours them when it refreshes the tick labels
just before saving. Editing tick labels directly on the Axes (e.g. with
`set_xticklabels()`) does not survive that refresh -- use `tick_relabel`
instead.

Multi-Panel Figures
-------------------
`finalise_plot()` works on a single Axes. For a figure with several
panels, finalise each panel with `axes_only=True` (axes-level styling
only: titles, labels, legends), then make the last call a normal
`finalise_plot()` carrying the figure-level arguments (`suptitle`,
`lfooter`, `rfooter`, `figsize`, ...), which also saves and closes
the figure:

```python
fig, (ax_left, ax_right) = plt.subplots(1, 2)
mg.line_plot(left_data, ax=ax_left)
mg.line_plot(right_data, ax=ax_right)
mg.finalise_plot(ax_left, title="Left Panel", ylabel="Index", axes_only=True)
mg.finalise_plot(
    ax_right,
    title="Right Panel",
    ylabel="Index",
    suptitle="Both Panels Together",  # also used for the filename
    lfooter="Australia. Seasonally adjusted.",
    rfooter="Source: ABS",
    figsize=(9, 4.5),
)
```

Convenience Finalisers
----------------------
For every plot function, there is a `*_finalise()` variant that combines
the plot and finalise steps:

- `bar_plot_finalise()`
- `fill_between_plot_finalise()`
- `growth_plot_finalise()`
- `line_plot_finalise()`
- `postcovid_plot_finalise()`
- `revision_plot_finalise()`
- `run_plot_finalise()`
- `seastrend_plot_finalise()`
- `series_growth_plot_finalise()`
- `summary_plot_finalise()`

Multi-Plot Chaining
-------------------
Chain plotting operations together for batch processing:

- `plot_then_finalise()` -- chains a plot function with `finalise_plot()`
- `multi_start()` -- creates multiple plots with different start dates
- `multi_column()` -- creates separate plots for each DataFrame column

Settings and Configuration
--------------------------
Manage global defaults for figure size, colors, output directory, etc.:

```python
mg.set_setting("figsize", (10, 5))
mg.set_setting("dpi", 150)
mg.set_chart_dir("./charts")

# Get current setting
current_dpi = mg.get_setting("dpi")
```

Color Utilities
---------------
Built-in support for Australian state/territory and political party colors:

```python
mg.get_color("NSW")           # Returns 'deepskyblue'
mg.get_color("Labor")         # Returns Labor party color
mg.colorise_list(["NSW", "VIC", "QLD"])  # Returns list of colors
```

Documentation
-------------
API documentation is generated from docstrings using pdoc. To view locally:

```bash
# Generate and serve docs
uv run pdoc src/mgplot

# Or open the pre-built docs
open docs/mgplot.html
```

Development
-----------
```bash
# Install dependencies
uv sync

# Run type checking
uv run pyright src/

# Run linting
uv run ruff check src/
uv run ruff format src/
```

License
-------
MIT License - see LICENSE file for details.

---
