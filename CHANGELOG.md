Version 0.2.30 - released 21-Jul-2026 (Canberra, Australia)

* enhancement
    - vertical lines added through the axvline keyword argument to
      finalise_plot() can now carry a text label, placed just to the right
      of the line and rotated to read bottom-to-top. Three new keys are
      recognised in an axvline dict, and are removed before the rest of the
      dict is passed to matplotlib:
        - text: the label itself. Without it, an axvline behaves exactly as
          it did before.
        - loc: where the label sits, one of "auto" (the default), "top" or
          "bottom". "auto" samples the plotted data in a narrow band around
          the line and anchors the label at whichever end has more room
          between the data and the axis limit; lines (from line plots) and
          rectangles (from bar plots) are both measured, and where nothing
          is measurable it falls back to "top".
        - text_kwargs: a dict merged into the underlying text call, which
          overrides any of the defaults - xx-small, rotated 90 degrees, and
          coloured to match the line.
      The label is anchored with x in data coordinates and y in axes
      coordinates, so it stays pinned to the top or bottom of the plot if
      the y-limits change afterwards. As axvline already accepted a sequence
      of dicts, several labelled lines can be placed in one call. Labels are
      not de-collided against each other; use an explicit loc if they crowd.
      A bad loc, a non-dict text_kwargs, or loc/text_kwargs given without any
      text all raise, as each is a typo rather than a choice.

---

Version 0.2.29 - released 30-Jun-2026 (Canberra, Australia)

* bug fix
    - finalise_plot() now accepts pandas Period values in the xlim and
      xticks keyword arguments. On a period-mapped axes (one built from a
      PeriodIndex) each Period is converted to its ordinal before being
      passed to matplotlib, mirroring the existing handling for axvline and
      axvspan; the Period's freq must match the axes' stashed freq, otherwise
      a clear ValueError is raised. Previously a Period in xlim/xticks reached
      matplotlib untranslated and raised a cryptic "ufunc 'isfinite' not
      supported" TypeError. The xlim/xticks type hints also accept int now,
      alongside float and Period.

---

Version 0.2.28 - released 20-Jun-2026 (Canberra, Australia)

* enhancement
    - end-of-line value annotations in line_plot() (and everything that
      routes through it, including growth_plot() and seastrend_plot())
      are now de-collided automatically. line_plot() registers the label
      artists on the axes and finalise_plot() spreads them once the figure
      layout is final, so the de-collision is measured against what is
      actually saved. The algorithm works in display coordinates:
        - a label that overlaps another label or a plotted line (over its
          own horizontal span) is nudged vertically by at most its own
          height to find a clear slot;
        - if that fails and the line ends within near_end (default 0.1) of
          the data width from the right edge, the label is snapped across
          to the rightmost data point and stacked vertically with the other
          end-of-axes labels;
        - if that fails for an interior label, the position with the most
          clearance is kept (overlap is accepted rather than moving the
          label off its line end);
        - line avoidance never applies to a label sitting at the last data
          point, whose text extends into the right margin.
      Added a near_end keyword to LineKwargs to tune the snap threshold.
      New module annotation_utils.py implements the resolver; new tests in
      test/test_annotation_collision.py.
    - revision_plot() (and revision_plot_finalise()) now default near_end
      to 0.0 instead of inheriting the 0.1 default, so the near-identical
      vintage labels that bunch at the right edge are no longer snapped and
      stacked against the right border. Callers can still pass near_end to
      override.
    - tweaked the default colour palettes in settings.py: the single-series
      colour is now "blue" (was "#dd0000"), and the 5-series palette uses
      "cornflowerblue" and "brown" in place of "seagreen" and "#dd0000".

---

Version 0.2.27 - released 19-Jun-2026 (Canberra, Australia)

* bug fix
    - get_color_list() in utilities.py now uses the matplotlib.colormaps
      registry (colormaps["nipy_spectral"]) instead of the removed
      matplotlib.cm.get_cmap(). cm.get_cmap was deprecated in matplotlib
      3.7 and removed in 3.9; this restored colour generation for charts
      with more series than the predefined palettes cover under
      matplotlib >= 3.9 (tested against 3.11.0)

---

Version 0.2.26 - released 5-Jun-2026 (Canberra, Australia)

* enhancement
    - added horizontal=True to bar_plot() (and bar_plot_finalise()):
      plots grouped or stacked horizontal bars with category labels on
      the y-axis and values along the x-axis. Designed for categorical
      (string-indexed) data - ranked states, industries, expenditure
      classes and the like. Bar annotations are placed at the bar ends
      (or within bars), vertically centred. Sign-aware stacking
      (negatives leftward, positives rightward) works as for vertical
      stacked bars. horizontal=True with a PeriodIndex warns and falls
      back to a vertical plot - period tick labelling is x-axis only
    - bar_plot() with a single series now accepts one colour per bar:
      if color is a sequence whose length matches the data, each bar is
      painted individually (e.g. state colours on a ranked horizontal
      bar chart). The in-bar annotation stroke effect picks the matching
      per-bar colour. Multi-series colour semantics are unchanged
    - added test/test_bar_horizontal.py covering string-index labels,
      annotations, grouped/stacked, negative stacking, the PeriodIndex
      fallback, per-bar colours, and label survival through
      finalise_plot()

---

Version 0.2.25 - released 5-Jun-2026 (Canberra, Australia)

* enhancement
    - added tick_relabel keyword argument to line_plot(), bar_plot(),
      growth_plot(), fill_between_plot() and run_plot() (and their
      *_finalise variants): a callable applied to each generated x-axis
      tick label after the contextual labellers have run (e.g. shorten
      4-digit years to 2 digits)
    - tick-label options (max_ticks, label rotation, tick_relabel) are
      now stashed on the Axes by set_labels() and honoured when
      finalise_plot() refreshes the labels before saving. Previously the
      refresh regenerated labels with hard-coded defaults (max_ticks=10,
      rotation=0), silently discarding per-plot settings
    - added register_label_options() / get_label_options() to
      axis_utils.py to support the above
    - keyword checking now validates Callable annotations (checks
      callability; previously a parameterized Callable would error)
    - added test/test_tick_relabel.py covering tick_relabel, max_ticks
      and label_rotation persistence through finalise_plot(), and
      correct-figure close behaviour
    - documented tick labelling and the multi-panel axes_only pattern
      in README.md (new "Axis Tick Labels" and "Multi-Panel Figures"
      sections)

* bug fix
    - bar_plot() applied label_rotation via plt.xticks(), which targets
      pyplot's current axes rather than the axes being plotted (wrong
      panel in multi-axes figures), and the rotation was then lost when
      finalise_plot() refreshed PeriodIndex labels. Rotation now goes
      via the stashed label options (PeriodIndex) or set_xticklabels()
      (string index)
    - finalise_plot() closed pyplot's current figure (plt.close()) rather
      than the figure belonging to the axes being finalised; it now closes
      the correct figure (walking up from a SubFigure if necessary)

---

Version 0.2.24 - released 4-Jun-2026 (Canberra, Australia)

* enhancement
    - added the chart_subdir() context manager to settings.py. It
      temporarily redirects chart output to a subdirectory of the current
      chart_dir, optionally clearing the subdirectory of image files on
      entry (clear=True), and restores the previous chart directory on
      exit, even if an exception is raised. Yields the subdirectory path.
      Useful in notebooks that group saved charts into per-topic
      subdirectories
    - added test/test_chart_subdir.py covering redirect/restore,
      exception safety, clear=True semantics and nested contexts
    - sorted __all__ in __init__.py (removed a duplicate "run_plot"
      entry), fixing a pre-existing RUF022 lint error
    - resolved all remaining mypy/pyright errors with runtime type
      narrowing (no casts): plot_latest_datapoint() in summary_plot.py
      now verifies datapoints are numeric (raising TypeError otherwise)
      before calling float(), and apply_splat_kwargs() in
      finalise_plot.py narrows dynamically-fetched kwarg values before
      passing them to _apply_splat()

---

Version 0.2.23 - released 24-Apr-2026 (Canberra, Australia)

* bug fix
    - finalise_plot() now refreshes PeriodIndex x-axis ticks after applying
      late-stage splat kwargs (axvspan, axvline). Previously, an axvspan or
      axvline that extended the view beyond the plotted data (e.g. a
      recession shade for dates before the series starts) would widen the
      xlim but leave the tick labels frozen at the original data range
    - a Period passed to axvspan/axvline now also widens the stashed period
      range, so tick labels cover the span even when matplotlib's auto-scale
      does not visibly extend the view

* enhancement
    - factored label regeneration out of set_labels() into the new
      refresh_period_labels() helper in axis_utils
    - added axes_only=True flag to finalise_plot() that suppresses all
      figure-level side effects (fig.set_size_inches, fig.tight_layout,
      fig.suptitle, header/footer fig.text, savefig, plt.show, plt.close).
      Use when finalising individual axes inside a multi-panel figure
      created with plt.subplots — the caller manages figure-level layout
      and saving themselves
    - added test_axvspan_period_widens_ticks and test_axes_only_preserves_figure
      to test/test_splat_sequences.py
    - added filename kwarg to finalise_plot() that overrides the title-derived
      stem used in the saved file's name. The override is sanitized and still
      composed with pre_tag/tag/file_type, so existing tagging behaviour is
      preserved

---

Version 0.2.22 - released 22-Apr-2026 (Canberra, Australia)

* bug fix
    - finalise_plot() now converts pandas Period values passed to axvline
      (x) and axvspan (xmin, xmax) into their integer ordinals, matching
      the ordinal-mapped x-axis used for PeriodIndex plots

* enhancement
    - axis_utils now stashes (freq, min_ordinal, max_ordinal) on any Axes
      that mgplot period-maps, via register_period_axes() / get_period_axes()
    - set_labels() registers the PeriodIndex and uses the union of the
      stashed ordinal range and the current xlim when building tick labels
    - plotting a second PeriodIndex with a different freq onto the same
      axes now raises ValueError (ordinals live in different spaces)
    - finalise_plot() raises ValueError when a Period passed to
      axvline/axvspan has a freq that does not match the axes' stashed freq;
      axes without a stash (e.g. external matplotlib axes) retain the
      trust-the-programmer behaviour and just use Period.ordinal
    - added freq-mismatch tests to test/test_splat_sequences.py

---

Version 0.2.21 - released 17-Mar-2026 (Canberra, Australia)

* enhancement
    - axhline, axvline, axhspan, axvspan in finalise_plot() now accept
      a sequence of dicts to draw multiple lines/spans in a single call,
      in addition to the existing single dict usage
    - added test/test_splat_sequences.py
    - fixed FURB110 ruff warnings (ternary if replaced with or operator)

---

Version 0.2.20 - released 25-Feb-2026 (Canberra, Australia)

* bug fix
    - fixed map_stringindex() to detect PyArrow-backed string dtypes
      (e.g. "string", "large_string[pyarrow]") in addition to legacy "object" dtype,
      using pd.api.types.is_string_dtype() instead of direct dtype comparison

---

Version 0.2.19 - released 25-Feb-2026 (Canberra, Australia)

* bug fix
    - fixed bar_plot() to handle string index values (e.g. country names)
      by mapping to integer positions and restoring labels after plotting
    - fixed label_rotation kwarg being silently ignored due to internal
      key mismatch ("xlabel_rotation" vs "label_rotation")
    - added map_stringindex() to axis_utils.py
    - added test/test_bar_string_index.py

---

Version 0.2.18 - released 08-Jan-2026 (Canberra, Australia)

* bug fix
    - fixed type specification for axhspan, axvspan, axhline, axvline kwargs
      in FinaliseKwargs to allow None values
    - removed dead code in apply_splat_kwargs()

---

Version 0.2.17 - released 22-Dec-2025 (Canberra, Australia)

* minor changes
    - added axisbelow kwarg to finalise_plot() for setting ax.set_axisbelow(True)

---

Version 0.2.16 - released 22-Dec-2025 (Canberra, Australia)

* minor changes
    - added zorder kwarg to line_plot(), bar_plot(), and fill_between_plot()
    - zorder supports sequences for per-series values in multi-series plots
    - added test/test_zorder.py

---

Version 0.2.15 - released 15-Dec-2025 (Canberra, Australia)

* minor changes
    - added suptitle kwarg to finalise_plot() for setting fig.suptitle()
    - suptitle takes priority over title for save-to filename if present

---

Version 0.2.14 - released 10-Dec-2025 (Canberra, Australia)

* bug fix
    - fixed x-axis ticks not spanning full data range when plotting multiple
      series with different time spans on the same axes
    - added test/test_multi_series_ticks.py

---

Version 0.2.13 - released 06-Dec-2025 (Canberra, Australia)

* minor changes
    - added fill_between_plot() function wrapping matplotlib's fill_between
    - added fill_between_plot_finalise() convenience function
    - added FillBetweenKwargs TypedDict

---

Version 0.2.12 - released 26-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.12
    - added label_rotation parameter to BarKwargs for controlling x-axis label rotation
    - documentation updates

---

Version 0.2.11 - released 20-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.101
    - updates to postcovid_plot.py (further gnarly edge cases fixed)

---
Version 0.2.10 - released 20-Jul-2025 (Canberra, Australia)

* minor changes
    - version bump to 0.2.10
    - updates to postcovid_plot.py
    - documentation updates

---

Version 0.2.9 - released 19-Jul-2025 (Canberra, Australia)

* minor changes
    - renamed build-test.sh to build-all.sh
    - version bump to 0.2.9
    - minor code refactoring in postcovid_plot.py

---

Version 0.2.8 - released 18-Jul-2025 (Canberra, Australia)

* minor changes
    - added lint-all.sh script
    - refinements to utilities.py
    - minor code improvements in bar_plot.py, line_plot.py, and finalisers.py
    - documentation updates

---

Version 0.2.7 - released 17-Jul-2025 (Canberra, Australia)

* major changes
    - intensive code linting across all modules
    - significant refactoring in finalisers.py, multi_plot.py, and other core modules
    - improved code quality and consistency
    - documentation regenerated

---

Version 0.2.6 - released 15-Jul-2025 (Canberra, Australia)

* minor changes
    - fixed a glitch where an axhspan was not appearing
      in nthe legend.

---

Version 0.2.5 - released 22-Jun-2025 (Canberra, Australia)

* minor changes
    - Fixed the xlabel thing in finalise_plot().
    - Changed from using Series.plot() to Axes.plot(),
      in line_plot() to avoid pandas setting the 
      xlabel/ylabel
    - fixed a labelling error in summary_plot()
    - removed an imposed-legend from run_plot_finalise()
    - added the capacity to label the runs in the run_plot() legend.
    - small number of consequential changes.

---

Version 0.2.4 - released 21-Jun-2025 (Canberra, Australia)

* minor changes
    - Implemented more aggressive code linting in ruff.
      with all but a handful of ruff linting rules
      activated (see pyproject.toml and lint-all.sh)
    - retired pylint and black

---

Version 0.2.1 - released 19-Jun-2025 (Canberra Australia)

* minor changes
    - changed linting regime - resulted in numerous minor 
      changes.
    - other minor changes

---

Version 0.2.0 - released 18-Jun-2025 (Canberra Australia)

* minor changes
    - fixed a glitch with the scaled summary plot

---

Version 0.2.0a2 - released 18-Jun-2025 (Canberra Australia)

* major changes
    - rewrote dynamic type-checking, to leverage static type 
      definitions
    - enhanced static type information for kwargs in most cases
    - moved test code into a separate directory
    - unresolved issue with scaled z-score charts

---

Version 0.1.13 - released 15-Jun-2025 (Canberra Australia)

* major changes
    - changed xticks for PeriodIndex in line_plot, to do the 
      same as bar_plot().
    - Now all PeriodIndex charts should use this approach to
      the x-axis.

---
Version 0.1.12 - released 14-Jun-2025 (Canberra Australia)

* minor changes
    - chnaged default_rounding() to apply for negative numbers

---

Version 0.1.11 - released 11-Jun-2025 (Canberra Australia)

* minor changes
     - refinements to the build code.

---

Version 0.1.10 - released 11-Jun-2025 (Canberra, Australia)

* minor changes
     - refined transition argument checking.

---

Version 0.1.9 - released 11-Jun-2025 (Canberra, Australia)

* minor changes
     - added some limited type checking through the argument
       transitions in growth_plot(), although most of the
       code is in the kw_type_checking module.

---

Version 0.1.9 - released 10-Jun-2025 (Canberra, Australia)

* minor changes
     - code linting

---

Version 0.1.8 - released 10-Jun-2025 (Canberra, Australia)

* major changes
     - standardised keyword argument names (in a separate module).
     - provided abbreviations for some keyword argument names.
     - removed legend keyword argument from data plotting functions 
       (ie. it is only implemented by finalise_plot())

---

Version 0.1.7 - released 06-Jun-2025 (Canberra, Australia)

* major changes
     - reworked growth_plot so that it used the line_plot()
       and bar_plot() functions. 

---

Version 0.1.6 - released 03-Jun-2025 (Canberra, Australia)

* minor changes
     - sorted the three remaining pylint issues with the 
       kw_type_checking module. Also improved error
       messages in the same module. 

---

Version 0.1.5 - released 02-Jun-2025 (Canberra, Australia)

* minor changes
     - minor changes to pyproject.toml and build-test.sh

---

Version 0.1.4 - released 01-Jun-2025 (Canberra, Australia)

* minor changes
     - changed the build-system
     - added dynamic version numbering to __init__.py
     - reworked annotations in the growth_plot.py module
       and the utilities module,
     - reworked kwargs validation in plot_then_finalise() 
     - typo in kw_type_checking.py
     - tightened up function chaining in the multi-plot modules
     - moved some default arguments from the finalisers module
       to the line_plot module.
     
---

Version 0.1.3 - released 31-May-2025 (Canberra, Australia)

* minor changes
     - changed defaults for postcovid_plot() to annotate series
     - changed line_plot() to bail early if nothing to plot
     - added a test to ignore empty axes objects in finalise_plot()
     - reduced the text size for runs in run_plot()
     - added "legend" to line_plot() and the growth plots.
     - if the plot function and the finalise_plot() function have
       kwargs in common, they will be handled by plot() and not
       sent to finalise plot (done by plot_then_finalise())
---

Version 0.1.2 - released 30-May-2025 (Canberra, Australia)

* minor changes
     - fixed an incorrect typing-gate in run_plot()
     - removed repeated version code in __init__.py
     - added "numpy-typing" to pyproject.toml
     - added a warning if ylabel set in series_growth_plot_finalise()
     - added legend=True default argument to raw_growth_plot()
---

Version 0.1.1 - released 29-May-2025 (Canberra, Australia)

* minor changes
     - added additional documentation
     - disclosed additional variables in the API
     - standardised the naming of the internal ExpectedTypeDicts
---

Version 0.1.0 - released 28-May-2025 (Canberra, Australia)

---
