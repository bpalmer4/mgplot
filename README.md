mgplot
======

Description
-----------
mgplot is an open-source python frontend for the matplotlib 
package to:
1. produce charts that can be a little difficult or tricky to 
   produce directly, 
2. finalise charts with titles, xlabels, ylabels, etc., while 
3. minimising code duplication, and maintaining a common plot
   style or look-and-feel.

Import
------
```
import mgplot as mg
```

Functions
---------
- set_chart_dir(chart_dir: str) - set the name of the global chart directory.
- clear_chart_dir() - Remove all graph-image files from the global chart_dir.
- finalise_plot(axes: plt.Axes, **kwargs) - this is the core method to finalise 
  and save plots to the file system. The filename for the saved plot is 
  constructed from the global chart_dir, the plot's title, any specified tag 
  text, and the file_type for the plot. 
  The following arguments may be passed in kwargs:
   - title: str - plot title, also used to create the save file name
   - xlabel: str - text label for the x-axis
   - ylabel: str - label for the y-axis
   - pre_tag: str - text before the title in file name
   - tag: str - text after the title in the file name 
     (useful for ensuring that same titled charts do not over-write)
   - chart_dir: str - location of the chart directory
   - file_type: str - specify a file type - eg. 'png' or 'svg'
   - lfooter: str - text to display on bottom left of plot
   - rfooter: str - text to display of bottom right of plot
   - lheader: str - text to display on top left of plot
   - rheader: str - text to display of top right of plot
   - figsize: tuple[float, float] - figure size in inches - eg. (8, 4)
   - show: bool - whether to show the plot or not
   - zero_y: bool - ensure y=0 is included in the plot.
   - y0: bool - highlight the y=0 line on the plot (if in scope)
   - x0: bool - highlights the x=0 line on the plot
   - dont_save: bool - dont save the plot to the file system
   - dont_close: bool - dont close the plot
   - dpi: int - dots per inch for the saved chart
   - legend: dict - arguments to pass to axes.legend()
   - axhspan: dict - arguments to pass to axes.axhspan()
   - axvspan: dict - arguments to pass to axes.axvspan()
   - axhline: dict - arguments to pass to axes.axhline()
   - axvline: dict - arguments to pass to axes.axvline()
   - ylim: tuple[float, float] - set lower and upper y-axis limits
   - xlim: tuple[float, float] - set lower and upper x-axis limits


For more information
--------------------
- to do

---
