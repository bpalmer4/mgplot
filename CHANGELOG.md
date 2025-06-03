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
