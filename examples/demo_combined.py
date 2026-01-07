## To run the demo examples, install the sofastats_examples package
## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py

from webbrowser import open_new_tab

from sofastats.output.charts.bar import SimpleBarChartDesign
from sofastats.output.charts.box_plot import ClusteredBoxplotChartDesign
from sofastats.output.stats.anova import AnovaDesign
from sofastats.output.tables.cross_tab import CrossTabDesign
from sofastats.output.tables.freq import FrequencyTableDesign
from sofastats.output.tables.interfaces import Column, Metric, Row, SortOrder
from sofastats.output.utils import get_report
from sofastats.stats_calc.interfaces import BoxplotType

from sofastats_examples.scripts.conf import output_folder, people_csv_file_path, sort_orders_yaml_file_path

def get_simple_bar_chart(csv_file_path):
    chart_design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    return chart_design

def get_cross_tab(csv_file_path):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable='Country', has_total=True,
        child=Row(variable='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable='Car')

    col_variables_design_1 = Column(variable='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    table_design = CrossTabDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='default',
        decimal_points=2,
    )
    return table_design

def get_clustered_boxplot(csv_file_path):
    chart_design = ClusteredBoxplotChartDesign(
        csv_file_path=csv_file_path,
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
    return chart_design

def get_simple_freq_tbl(csv_file_path):
    row_variables_design_1 = Row(variable='Country', has_total=True, child=Row(variable='Handedness', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable='Age Group', has_total=True, sort_order=SortOrder.CUSTOM)

    table_design = FrequencyTableDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        include_column_percent=True,
        decimal_points=3,
    )
    return table_design

def get_anova(csv_file_path):
    stats_design = AnovaDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='prestige_screen',
        grouping_field_name='Country',
        group_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    return stats_design

