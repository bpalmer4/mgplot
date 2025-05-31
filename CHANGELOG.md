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
     - removed duplicate versioning code in __init__.py
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
