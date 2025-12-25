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
