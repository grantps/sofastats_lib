"""
When we chart some data we might produce one individual chart or a series of charts
(for example, one chart per country).

Each chart might have one series of values or multiple series. A clustered bar chart,
for example, will have one series per group.

Sometimes we will have multiple charts and each chart will have multiple series
e.g. we have a chart per gender and within each chart a series per country.

Sometimes we will have a single chart with only one series of data.

So ...

A charting_spec is the top-level object.
It defines attributes shared across all individual charts:
  * x_axis_specs or slice_category_specs defining val and label (split into lines)
and depending on type of chart:
  * x_axis_title
  * y_axis_title
  * rotate_x_labels
  * show_n_records
  * show_borders
  * x_axis_font_size
  * etc.
It is often extended e.g. for bar, line etc.
Will have two children: Axes vs NoAxes (pie) versions
Axes will have lots of children - bar, line, area etc.
indiv_chart_specs (often just one) are below charting_spec
Each indiv_chart_spec has data_series_specs below (often just one)
Each data_series_item amount, label, and tooltip
"""
