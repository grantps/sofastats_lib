## To run the demo examples, install the sofastats_examples package
## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py

import sqlite3 as sqlite

from sofastats.conf.main import ChartMetric, SortOrder
# noinspection PyUnresolvedReferences
from sofastats.output.charts import area, bar, box_plot, histogram, line, pie, scatter_plot  ## needed so singledispatch registration can occur
from sofastats.output.charts.area import AreaChartDesign, MultiChartAreaChartDesign
from sofastats.output.charts.bar import (
    ClusteredBarChartDesign, MultiBarChartDesign, MultiChartClusteredBarChartDesign, SimpleBarChartDesign)
from sofastats.output.charts.box_plot import BoxplotChartDesign, ClusteredBoxplotChartDesign
from sofastats.output.charts.histogram import HistogramChartDesign, MultiChartHistogramChartDesign
from sofastats.output.charts.line import (LineChartDesign,
    MultiChartLineChartDesign, MultiChartMultiLineChartDesign, MultiLineChartDesign)
from sofastats.output.charts.pie import MultiChartPieChartDesign, PieChartDesign
from sofastats.output.charts.scatter_plot import (BySeriesScatterChartDesign,
    MultiChartBySeriesScatterChartDesign, MultiChartScatterChartDesign, SimpleScatterChartDesign)
from sofastats.stats_calc.interfaces import BoxplotType

from sofastats_examples.scripts.conf import (education_csv_file_path, output_folder, people_csv_file_path,
    sort_orders_yaml_file_path, sports_csv_file_path, sqlite_demo_db_file_path)

def simple_bar_chart_from_sqlite_db(sqlite_cur):
    chart_design = SimpleBarChartDesign(
        cur=sqlite_cur,
        database_engine_name='sqlite',
        source_table_name='people',
        output_file_path=output_folder / 'demo_simple_bar_chart_from_sqlite_db.html',
        output_title="Simple Bar Chart (Frequencies) from SQLite",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
        y_axis_title='Count',  ## defaults to Frequency if metric is FREQ (the default)
    )
    chart_design.make_output()

def simple_bar_chart_from_csv(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_from_csv.html',
        output_title="Simple Bar Chart (Frequencies)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def simple_bar_chart_percents_from_csv(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_percents_from_csv.html',
        output_title="Simple Bar Chart (Percents)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        metric=ChartMetric.PCT,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def simple_bar_chart_averages_from_csv(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_averages_from_csv.html',
        output_title="Simple Bar Chart (Averages)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        metric=ChartMetric.AVG,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def simple_bar_chart_sums_from_csv(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_sums_from_csv.html',
        output_title="Simple Bar Chart (Sums)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        metric=ChartMetric.SUM,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def simple_bar_chart_lots_of_x_vals(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_wide.html',
        output_title="Simple Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='prestige_screen',
        category_field_name='Car',
        category_sort_order=SortOrder.VALUE,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_bar_chart(csv_file_path):
    chart_design = MultiBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_bar_chart.html',
        output_title="Multi Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def clustered_bar_chart(csv_file_path):
    chart_design = ClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_clustered_bar_chart.html',
        output_title="Clustered Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_clustered_bar_chart(csv_file_path):
    chart_design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_clustered_bar_chart.html',
        output_title="Multi Chart Clustered Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_clustered_percents_bar_chart(csv_file_path):
    chart_design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_clustered_percents_bar_chart.html',
        output_title="Multi Chart Clustered Bar Chart (Percents)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        metric=ChartMetric.PCT,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def line_chart(csv_file_path):
    chart_design = LineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_line_chart.html',
        output_title="Line Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def line_chart_time_series(csv_file_path):
    chart_design = LineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_line_chart_time_series.html',
        output_title="Line Chart Time Series",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Registration Date',
        category_sort_order=SortOrder.VALUE,
        is_time_series=True,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def line_chart_time_series_rotated_labels(csv_file_path):
    chart_design = LineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_line_chart_time_series_rotated_labels.html',
        output_title="Line Chart Time Series (Rotated Labels)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Registration Date',
        category_sort_order=SortOrder.VALUE,
        is_time_series=True,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=True,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_line_chart(csv_file_path):
    chart_design = MultiLineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_line_chart.html',
        output_title="Multi-Line Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_line_chart(csv_file_path):
    chart_design = MultiChartLineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_line_chart.html',
        output_title="Multi Chart Line Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_multi_line_chart(csv_file_path):
    chart_design = MultiChartMultiLineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_multi_line_chart.html',
        output_title="Multi-Chart Multi-Line Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Age Group',
        chart_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_multi_line_chart_time_series(csv_file_path):
    chart_design = MultiChartMultiLineChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_multi_line_chart_time_series.html',
        output_title="Multi-Chart Multi-Line Chart Time Series",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Registration Date',
        category_sort_order=SortOrder.VALUE,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Age Group',
        chart_sort_order=SortOrder.CUSTOM,
        is_time_series=True,
        show_major_ticks_only=True,
        show_markers=True,
        show_smooth_line=False,
        show_trend_line=False,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def area_chart(csv_file_path):
    chart_design = AreaChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_area_chart.html',
        output_title="Area Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_area_chart(csv_file_path):
    chart_design = MultiChartAreaChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_area_chart.html',
        output_title="Area Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        is_time_series=False,
        show_major_ticks_only=True,
        show_markers=True,
        rotate_x_labels=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def pie_chart(csv_file_path):
    chart_design = PieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart.html',
        output_title="Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Country',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def multi_chart_pie_chart(csv_file_path):
    chart_design = MultiChartPieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart.html',
        output_title="Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    chart_design.make_output()

def simple_scatterplot(csv_file_path):
    chart_design = SimpleScatterChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_scatterplot.html',
        output_title="Single Series Scatterplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        show_dot_borders=True,
        show_n_records=True,
        show_regression_line=True,
        x_axis_font_size=10,
    )
    chart_design.make_output()

def by_series_scatterplot(csv_file_path):
    chart_design = BySeriesScatterChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_by_series_scatterplot.html',
        output_title="Multi-Series Scatterplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        show_dot_borders=True,
        show_n_records=True,
        show_regression_line=True,
        x_axis_font_size=10,
    )
    chart_design.make_output()

def multi_chart_scatterplot(csv_file_path):
    chart_design = MultiChartScatterChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_scatterplot.html',
        output_title="Multi-Chart Scatterplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        show_dot_borders=True,
        show_n_records=True,
        show_regression_line=True,
        x_axis_font_size=10,
    )
    chart_design.make_output()

def multi_chart_by_series_scatterplot(csv_file_path):
    chart_design = MultiChartBySeriesScatterChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_by_series_scatterplot.html',
        output_title="Multi-Chart Multi-Series Scatterplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Home Location Type',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        show_dot_borders=True,
        show_n_records=True,
        show_regression_line=True,
        x_axis_font_size=10,
    )
    chart_design.make_output()

def histogram_chart(csv_file_path):
    chart_design = HistogramChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_histogram.html',
        output_title="Histogram Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        show_borders=False,
        show_n_records=True,
        show_normal_curve=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

def multi_chart_histogram(csv_file_path):
    chart_design = MultiChartHistogramChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_histogram.html',
        output_title="Multi Chart Histogram Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        show_borders=False,
        show_n_records=True,
        show_normal_curve=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

def boxplot_chart(csv_file_path):
    chart_design = BoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_boxplot.html',
        output_title="Boxplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Handedness',
        category_sort_order=SortOrder.CUSTOM,
        boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

def boxplot_chart_narrow_labels(csv_file_path):
    chart_design = BoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_boxplot_narrow_labels.html',
        output_title="Boxplot (narrow)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Country',
        category_sort_order=SortOrder.CUSTOM,
        boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

def boxplot_chart_very_wide(csv_file_path):
    chart_design = BoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_boxplot_very_wide.html',
        output_title="Boxplot (very wide)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Car',
        category_sort_order=SortOrder.CUSTOM,
        boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

def clustered_boxplot(csv_file_path):
    chart_design = ClusteredBoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multiseries_boxplot.html',
        output_title="Multi-Series Boxplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Country',
        series_field_name='Home Location Type',
        series_sort_order=SortOrder.CUSTOM,
        category_sort_order=SortOrder.CUSTOM,
        boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    chart_design.make_output()

