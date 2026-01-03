from pathlib import Path
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

examples_folder = Path.cwd().parent
files_folder = examples_folder / 'files'
output_folder = examples_folder / 'output'
sort_orders_yaml_file_path = files_folder / 'sort_orders.yaml'
people_csv_file_path = files_folder / 'people.csv'

def simple_bar_chart_from_sqlite_db(sqlite_cur):
    chart_design = SimpleBarChartDesign(
        cur=sqlite_cur,
        database_engine_name='sqlite',
        source_table_name='people',
        output_file_path=output_folder / 'demo_simple_bar_chart_from_sqlite_db.html',
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
        output_file_path=output_folder / 'test_simple_bar_chart_wide.html',
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
        output_file_path=output_folder / 'test_multi_bar_chart.html',
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
        output_file_path=output_folder / 'test_clustered_bar_chart.html',
        output_title="Clustered Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Handedness',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Sleep Group',
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
        output_file_path=output_folder / 'test_multi_chart_clustered_bar_chart.html',
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
        output_file_path=output_folder / 'test_multi_chart_clustered_percents_bar_chart.html',
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

# def line_chart():
#     chart_design = LineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_line_chart.html'),
#         output_title="Line Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def line_chart_time_series():
#     chart_design = LineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_line_chart_time_series.html'),
#         output_title="Line Chart Time Series",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Event Date',
#         category_sort_order=SortOrder.VALUE,
#         is_time_series=True,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def line_chart_time_series_rotated_labels():
#     chart_design = LineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_line_chart_time_series_rotated_labels.html'),
#         output_title="Line Chart Time Series (Rotated Labels)",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Event Date',
#         category_sort_order=SortOrder.VALUE,
#         is_time_series=True,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=True,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_line_chart():
#     chart_design = MultiLineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_line_chart.html'),
#         output_title="Multi-Line Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         series_field_name='Country',
#         series_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_chart_line_chart():
#     chart_design = MultiChartLineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_line_chart.html'),
#         output_title="Multi Chart Line Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         chart_field_name='Country',
#         chart_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_chart_multi_line_chart():
#     chart_design = MultiChartMultiLineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_multi_line_chart.html'),
#         output_title="Multi-Chart Multi-Line Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         series_field_name='Country',
#         series_sort_order=SortOrder.CUSTOM,
#         chart_field_name='Age Group',
#         chart_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_chart_multi_line_chart_time_series():
#     chart_design = MultiChartMultiLineChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_multi_line_chart_time_series.html'),
#         output_title="Multi-Chart Multi-Line Chart Time Series",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Event Date',
#         category_sort_order=SortOrder.VALUE,
#         series_field_name='Country',
#         series_sort_order=SortOrder.CUSTOM,
#         chart_field_name='Age Group',
#         chart_sort_order=SortOrder.CUSTOM,
#         is_time_series=True,
#         show_major_ticks_only=True,
#         show_markers=True,
#         show_smooth_line=False,
#         show_trend_line=False,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def area_chart():
#     chart_design = AreaChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_area_chart.html'),
#         output_title="Area Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_chart_area_chart():
#     chart_design = MultiChartAreaChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_area_chart.html'),
#         output_title="Area Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         chart_field_name='Country',
#         chart_sort_order=SortOrder.CUSTOM,
#         is_time_series=False,
#         show_major_ticks_only=True,
#         show_markers=True,
#         rotate_x_labels=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def pie_chart():
#     chart_design = PieChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_pie_chart.html'),
#         output_title="Pie Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         rotate_x_labels=False,
#         show_borders=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def multi_chart_pie_chart():
#     chart_design = MultiChartPieChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_pie_chart.html'),
#         output_title="Pie Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         chart_field_name='Country',
#         chart_sort_order=SortOrder.CUSTOM,
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         rotate_x_labels=False,
#         show_borders=False,
#         show_n_records=True,
#         x_axis_font_size=12,
#         y_axis_title='Freq',
#     )
#     chart_design.make_output()
#
# def simple_scatterplot():
#     chart_design = SimpleScatterChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_simple_scatterplot.html'),
#         output_title="Single Series Scatterplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         x_field_name='Age',
#         y_field_name='Weight Time 1',
#         show_dot_borders=True,
#         show_n_records=True,
#         show_regression_line=True,
#         x_axis_font_size=10,
#     )
#     chart_design.make_output()
#
# def by_series_scatterplot():
#     chart_design = BySeriesScatterChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_by_series_scatterplot.html'),
#         output_title="Multi-Series Scatterplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         x_field_name='Age',
#         y_field_name='Weight Time 1',
#         series_field_name='Gender',
#         series_sort_order=SortOrder.CUSTOM,
#         show_dot_borders=True,
#         show_n_records=True,
#         show_regression_line=True,
#         x_axis_font_size=10,
#     )
#     chart_design.make_output()
#
# def multi_chart_scatterplot():
#     chart_design = MultiChartScatterChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_scatterplot.html'),
#         output_title="Multi-Chart Scatterplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         x_field_name='Age',
#         y_field_name='Weight Time 1',
#         chart_field_name='Gender',
#         chart_sort_order=SortOrder.CUSTOM,
#         show_dot_borders=True,
#         show_n_records=True,
#         show_regression_line=True,
#         x_axis_font_size=10,
#     )
#     chart_design.make_output()
#
# def multi_chart_by_series_scatterplot():
#     chart_design = MultiChartBySeriesScatterChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_by_series_scatterplot.html'),
#         output_title="Multi-Chart Multi-Series Scatterplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         x_field_name='Age',
#         y_field_name='Weight Time 1',
#         series_field_name='Country',
#         series_sort_order=SortOrder.CUSTOM,
#         chart_field_name='Gender',
#         chart_sort_order=SortOrder.CUSTOM,
#         show_dot_borders=True,
#         show_n_records=True,
#         show_regression_line=True,
#         x_axis_font_size=10,
#     )
#     chart_design.make_output()
#
# def histogram_chart():
#     chart_design = HistogramChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_histogram.html'),
#         output_title="Histogram Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         show_borders=False,
#         show_n_records=True,
#         show_normal_curve=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()
#
# def multi_chart_histogram():
#     chart_design = MultiChartHistogramChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multi_chart_histogram.html'),
#         output_title="Multi Chart Histogram Chart",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         chart_field_name='Gender',
#         chart_sort_order=SortOrder.CUSTOM,
#         show_borders=False,
#         show_n_records=True,
#         show_normal_curve=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()
#
# def boxplot_chart():
#     chart_design = BoxplotChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_boxplot.html'),
#         output_title="Boxplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         category_field_name='Web Browser',
#         category_sort_order=SortOrder.CUSTOM,
#         boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
#         show_n_records=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()
#
# def boxplot_chart_narrow_labels():
#     chart_design = BoxplotChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_boxplot_narrow_labels.html'),
#         output_title="Boxplot (narrow)",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         category_field_name='Country',
#         category_sort_order=SortOrder.CUSTOM,
#         boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
#         show_n_records=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()
#
# def boxplot_chart_very_wide():
#     chart_design = BoxplotChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_boxplot_very_wide.html'),
#         output_title="Boxplot (very wide)",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         category_field_name='Car',
#         category_sort_order=SortOrder.CUSTOM,
#         boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
#         show_n_records=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()
#
# def clustered_boxplot():
#     chart_design = ClusteredBoxplotChartDesign(
#         source_table_name='demo_tbl2',
#         output_file_path=Path('/home/g/Documents/sofastats/output/test_multiseries_boxplot.html'),
#         output_title="Multi-Series Boxplot",
#         show_in_web_browser=True,
#         sort_orders_yaml_file_path=sort_orders_yaml_file_path,
#         style_name='default',
#         field_name='Age',
#         category_field_name='Country',
#         series_field_name='Gender',
#         series_sort_order=SortOrder.CUSTOM,
#         category_sort_order=SortOrder.CUSTOM,
#         boxplot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
#         show_n_records=True,
#         x_axis_font_size=12,
#         decimal_points=3,
#     )
#     chart_design.make_output()

if __name__ == '__main__':
    sqlite_demo_db_file_path = files_folder / 'sofastats_demo.db'
    con = sqlite.connect(sqlite_demo_db_file_path)
    cur = con.cursor()

    # simple_bar_chart_from_sqlite_db(cur)
    simple_bar_chart_from_csv(people_csv_file_path)
    simple_bar_chart_percents_from_csv(people_csv_file_path)
    simple_bar_chart_averages_from_csv(people_csv_file_path)
    simple_bar_chart_sums_from_csv(people_csv_file_path)
    # simple_bar_chart_lots_of_x_vals(people_csv_file_path)
    # multi_bar_chart(people_csv_file_path)
    # clustered_bar_chart(people_csv_file_path)
    # multi_chart_clustered_bar_chart(people_csv_file_path)
    # multi_chart_clustered_percents_bar_chart(people_csv_file_path)

    # line_chart(people_csv_file_path)
    # line_chart_time_series(people_csv_file_path)
    # line_chart_time_series_rotated_labels(people_csv_file_path)
    # multi_line_chart(people_csv_file_path)
    # multi_chart_line_chart(people_csv_file_path)
    # multi_chart_multi_line_chart(people_csv_file_path)
    # multi_chart_multi_line_chart_time_series(people_csv_file_path)
    #
    # area_chart(people_csv_file_path)
    # multi_chart_area_chart(people_csv_file_path)
    #
    # pie_chart(people_csv_file_path)
    # multi_chart_pie_chart(people_csv_file_path)
    #
    # simple_scatterplot(people_csv_file_path)
    # by_series_scatterplot(people_csv_file_path)
    # multi_chart_scatterplot(people_csv_file_path)
    # multi_chart_by_series_scatterplot(people_csv_file_path)
    #
    # histogram_chart(people_csv_file_path)
    # multi_chart_histogram(people_csv_file_path)
    #
    # boxplot_chart(people_csv_file_path)
    # boxplot_chart_narrow_labels(people_csv_file_path)
    # boxplot_chart_very_wide(people_csv_file_path)
    # clustered_boxplot(people_csv_file_path)

    cur.close()
    con.close()
