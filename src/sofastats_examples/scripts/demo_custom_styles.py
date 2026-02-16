"""
Force it to look for horrific.yaml in the custom_styles subfolder of the home documents / sofastats folder.
If you succeed, you'll know why the style is called horrific ;-).
The point is to demonstrate each colour setting separately and obviously.
"""
from sofastats.output.charts.bar import MultiChartClusteredBarChartDesign, SimpleBarChartDesign
from sofastats.output.charts.box_plot import BoxplotChartDesign, ClusteredBoxplotChartDesign
from sofastats.output.charts.histogram import MultiChartHistogramChartDesign
from sofastats.output.charts.pie import MultiChartPieChartDesign
from sofastats.output.charts.scatter_plot import MultiChartBySeriesScatterChartDesign
from sofastats.output.stats.anova import AnovaDesign
from sofastats.output.tables.cross_tab import CrossTabDesign
from sofastats.output.tables.freq import FrequencyTableDesign
from sofastats.output.tables.interfaces import Column, Metric, Row, SortOrder
from sofastats.stats_calc.interfaces import BoxplotType

from sofastats_examples.scripts.conf import (
    education_csv_file_path, output_folder, people_csv_file_path, sports_csv_file_path, sort_orders_yaml_file_path)

def simple_bar_chart_from_csv(csv_file_path):
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_simple_bar_chart_from_csv.html',
        output_title="Simple Bar Chart (Frequencies)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='black_pastel',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        rotate_x_labels=False,
        show_borders=False,
        show_n_records=True,
        x_axis_font_size=12,
    )
    design.make_output()

def multi_chart_clustered_bar_chart_1(csv_file_path):
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_clustered_bar_chart_style1.html',
        output_title="Multi Chart Clustered Bar Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='black_pastel',
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
    design.make_output()

def multi_chart_clustered_bar_chart_2(csv_file_path):
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_clustered_bar_chart_style2.html',
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
        show_borders=True,
        show_n_records=True,
        x_axis_font_size=12,
    )
    design.make_output()

def multi_chart_pie_chart_1(csv_file_path):
    design = MultiChartPieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart_default.html',
        output_title="Multi-Chart Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        show_n_records=True,
    )
    design.make_output()

def multi_chart_pie_chart_2(csv_file_path):
    design = MultiChartPieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart_black_pastel.html',
        output_title="Multi-Chart Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='black_pastel',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        show_n_records=True,
    )
    design.make_output()

def multi_chart_pie_chart_3(csv_file_path):
    design = MultiChartPieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart_gray_spirals.html',
        output_title="Multi-Chart Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='gray_spirals',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        show_n_records=True,
    )
    design.make_output()

def multi_chart_pie_chart_4(csv_file_path):
    design = MultiChartPieChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pie_chart_red_spirals.html',
        output_title="Multi-Chart Pie Chart",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='red_spirals',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        show_n_records=True,
    )
    design.make_output()

def run_anova(csv_file_path):
    stats_design = AnovaDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_anova_age_by_country.html',
        output_title='ANOVA',
        show_in_web_browser=True,
        style_name='default',
        grouping_field_name='Country',
        grouping_field_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    stats_design.make_output()

def run_anova_black_pastel_style(csv_file_path):
    stats_design = AnovaDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_anova_age_by_country_black_pastel_style.html',
        output_title='ANOVA',
        show_in_web_browser=True,
        style_name='black_pastel',
        grouping_field_name='Country',
        grouping_field_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    stats_design.make_output()

def multi_chart_by_series_scatterplot(csv_file_path):
    chart_design = MultiChartBySeriesScatterChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multi_chart_by_series_scatterplot.html',
        output_title="Multi-Chart Multi-Series Scatterplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='black_pastel',
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

def multi_chart_histogram(csv_file_path):
    design = MultiChartHistogramChartDesign(
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
    design.make_output()

def box_plot_chart_narrow_labels(csv_file_path):
    design = BoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_box_plot_narrow_labels.html',
        output_title="Boxplot (narrow)",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Country',
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    design.make_output()

def clustered_box_plot(csv_file_path):
    design = ClusteredBoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multiseries_box_plot.html',
        output_title="Multi-Series Boxplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        field_name='Age',
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    design.make_output()

def clustered_box_plot_2(csv_file_path):
    design = ClusteredBoxplotChartDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_multiseries_box_plot_style2.html',
        output_title="Multi-Series Boxplot",
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='black_pastel',
        field_name='Age',
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
        show_n_records=True,
        x_axis_font_size=12,
        decimal_points=3,
    )
    design.make_output()

def run_simple_freq_tbl(csv_file_path):
    row_variables_design_1 = Row(variable_name='Country', has_total=True, child=Row(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM)

    table_design = FrequencyTableDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_freq_table_no_col_pct_from_item.html',
        output_title='Frequency Table',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        include_column_percent=True,
        decimal_points=3,
    )
    table_design.make_output()

def cross_tab_1(csv_file_path):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    design = CrossTabDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_main_cross_tab_black_pastel_style.html',
        output_title='Cross Tab',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='black_pastel',
        decimal_points=2,
    )
    design.make_output()

def cross_tab_2(csv_file_path):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    design = CrossTabDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_main_cross_tab_gray_spirals_style',
        output_title='Cross Tab',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='gray_spirals',
        decimal_points=2,
    )
    design.make_output()

def run():
    pass

    # simple_bar_chart_from_csv(people_csv_file_path)
    #
    # multi_chart_clustered_bar_chart_1(people_csv_file_path)
    # multi_chart_clustered_bar_chart_2(people_csv_file_path)
    #
    # multi_chart_pie_chart_1(sports_csv_file_path)
    # multi_chart_pie_chart_2(sports_csv_file_path)
    # multi_chart_pie_chart_3(sports_csv_file_path)
    # multi_chart_pie_chart_4(sports_csv_file_path)
    #
    # run_anova(people_csv_file_path)
    # run_anova_black_pastel_style(people_csv_file_path)
    # multi_chart_by_series_scatterplot(education_csv_file_path)
    # multi_chart_histogram(people_csv_file_path)
    # box_plot_chart_narrow_labels(people_csv_file_path)
    # clustered_box_plot(people_csv_file_path)
    # clustered_box_plot_2(people_csv_file_path)
    # run_simple_freq_tbl(people_csv_file_path)
    # cross_tab_1(people_csv_file_path)
    # cross_tab_2(people_csv_file_path)

if __name__ == '__main__':
    run()
