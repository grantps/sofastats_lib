# API Documentation

## Common Data Types
::: sofastats.conf.main.SortOrder

## Common Parameters
The parameters in `CommonDesign` are common to all output design dataclasses: 
::: sofastats.output.interfaces.CommonDesign

## Charts

### Area Charts
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`AreaChartDesign`][sofastats.output.charts.area.AreaChartDesign] for the parameters
configuring individual area chart designs.

::: sofastats.output.charts.area.AreaChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.area.MultiChartAreaChartDesign
    options:
        heading_level: 4
### Bar Charts
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`SimpleBarChartDesign`][sofastats.output.charts.bar.SimpleBarChartDesign] for the parameters
configuring individual bar chart designs.

::: sofastats.output.charts.bar.CommonBarDesign
    options:
        heading_level: 4
::: sofastats.output.charts.bar.SimpleBarChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.bar.MultiChartBarChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.bar.ClusteredBarChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.bar.MultiChartClusteredBarChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.bar.MultiChartClusteredBarChartDesign
    options:
        heading_level: 4

### Box Plots
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`BoxplotChartDesign`][sofastats.output.charts.box_plot.BoxplotChartDesign] for the parameters
configuring individual box plot chart designs.

::: sofastats.output.charts.box_plot.BoxplotChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.box_plot.ClusteredBoxplotChartDesign
    options:
        heading_level: 4

### Histograms
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`HistogramChartDesign`][sofastats.output.charts.histogram.HistogramChartDesign] for the parameters
configuring individual histogram chart designs.

::: sofastats.output.charts.histogram.HistogramChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.histogram.MultiChartHistogramChartDesign
    options:
        heading_level: 4

### Line Charts
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`LineChartDesign`][sofastats.output.charts.line.LineChartDesign] for the parameters
configuring individual line chart designs.

::: sofastats.output.charts.line.LineChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.line.MultiChartLineChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.line.MultiLineChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.line.MultiChartMultiLineChartDesign
    options:
        heading_level: 4

### Pie Charts
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`PieChartDesign`][sofastats.output.charts.pie.PieChartDesign] for the parameters
configuring individual pie chart designs.

::: sofastats.output.charts.pie.PieChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.pie.MultiChartPieChartDesign
    options:
        heading_level: 4

### Scatter Plots
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

See [`SimpleScatterChartDesign`][sofastats.output.charts.scatter_plot.SimpleScatterChartDesign] for the parameters
configuring individual scatter plot chart designs.

::: sofastats.output.charts.scatter_plot.SimpleScatterChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.scatter_plot.MultiChartScatterChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.scatter_plot.BySeriesScatterChartDesign
    options:
        heading_level: 4
::: sofastats.output.charts.scatter_plot.MultiChartBySeriesScatterChartDesign
    options:
        heading_level: 4

## Tables
See [`CommonDesign`][sofastats.output.interfaces.CommonDesign]
for the parameters common to all output design dataclasses in sofastats - for example, `style_name`.

`DimensionSpec` defines the main parameters of both the `Row` and `Column` table dimensions.
The only parameter `Row` and `Column` adds is the appropriate setting for `is_col`.

::: sofastats.output.tables.interfaces.DimensionSpec
    options:
        heading_level: 3
        filters: ["!.*"]  ## hides all methods
::: sofastats.output.tables.interfaces.Row
    options:
        heading_level: 3
::: sofastats.output.tables.interfaces.Column
    options:
        heading_level: 3
::: sofastats.output.tables.freq.FrequencyTableDesign
    options:
        heading_level: 3
        filters: ["!.*"]  ## hides all methods
::: sofastats.output.tables.cross_tab.CrossTabDesign
    options:
        heading_level: 3
        filters: ["!.*"]  ## hides all methods

## Statistical Tests

::: sofastats.output.stats.interfaces.CommonStatsDesign
    options:
        heading_level: 3

### ANOVA

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.anova.AnovaDesign
    options:
        heading_level: 4

### Chi Square

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.chi_square.ChiSquareDesign
    options:
        heading_level: 4

### Kruskal-Wallis H

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.kruskal_wallis_h.KruskalWallisHDesign
    options:
        heading_level: 4

### Mann-Whitney U

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.mann_whitney_u.MannWhitneyUDesign
    options:
        heading_level: 4

### Normality

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.normality.NormalityDesign
    options:
        heading_level: 4

### Pearson's R Correlation

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.pearsons_r.PearsonsRDesign
    options:
        heading_level: 4

### Spearman's R Correlation

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.spearmans_r.SpearmansRDesign
    options:
        heading_level: 4

### Independent Samples T-Test

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.ttest_indep.TTestIndepDesign
    options:
        heading_level: 4

### Wilcoxon Signed Ranks

See [`CommonStatsDesign`][sofastats.output.stats.interfaces.CommonStatsDesign]
for details of the `to_result()` method common to all stats output design dataclasses in sofastats.

::: sofastats.output.stats.wilcoxon_signed_ranks.WilcoxonSignedRanksDesign
    options:
        heading_level: 4
