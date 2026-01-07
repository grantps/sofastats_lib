## To run the demo examples, install the sofastats_examples package
## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py

import sqlite3 as sqlite

from sofastats.conf.main import DbeName, SortOrder
from sofastats.output.tables.cross_tab import CrossTabDesign
from sofastats.output.tables.freq import FrequencyTableDesign
from sofastats.output.tables.interfaces import Column, Metric, Row

from sofastats_examples.scripts.conf import (
    output_folder, people_csv_file_path, sort_orders_yaml_file_path, sqlite_demo_db_file_path)


def run_cross_tab_from_sqlite_db_filtered(sqlite_cur):
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
        cur=sqlite_cur,
        database_engine_name=DbeName.SQLITE,  ## or just the string 'sqlite'
        source_table_name='people',
        table_filter_sql="WHERE Car IN ('Porsche', 'Audi', 'Toyota', 'Aston Martin')",  ## must have backticks around entity names containing spaces in SQLite; no trailing commas - this is SQL not Python
        output_file_path=output_folder / 'demo_main_cross_tab_from_sqlite_db_filtered.html',
        output_title='Cross Tab from SQLite (Filtered by Car)',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='default',
        decimal_points=2,
    )
    table_design.make_output()

def run_cross_tab_from_sqlite_db(sqlite_cur):
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
        cur=sqlite_cur,
        database_engine_name=DbeName.SQLITE,  ## or just the string 'sqlite'
        source_table_name='people',
        output_file_path=output_folder / 'demo_main_cross_tab_from_sqlite_db.html',
        output_title='Cross Tab from SQLite',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='default',
        decimal_points=2,
    )
    table_design.make_output()

def run_cross_tab(csv_file_path):
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
        output_file_path=output_folder / 'demo_main_cross_tab.html',
        output_title='Cross Tab',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='default',
        decimal_points=2,
    )
    table_design.make_output()

def run_repeat_level_two_row_var_cross_tab(csv_file_path):
    """
    Repeated row level 2 was no issue BUT a bug in the col ordering
    """
    row_variables_design_1 = Row(variable='Country', has_total=True,
        child=Row(variable='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))

    col_variables_design_1 = Column(variable='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM,
        pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT])

    table_design = CrossTabDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_main_cross_tab_repeated_levels.html',
        output_title='Cross Tab (Repeated Levels)',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        column_variable_designs=[col_variables_design_1, ],
        style_name='grey_spirals',
        decimal_points=2,
        debug=False,
        verbose=False,
    )
    table_design.make_output()

def run_simple_freq_tbl(csv_file_path):
    row_variables_design_1 = Row(variable='Country', has_total=True, child=Row(variable='Handedness', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable='Age Group', has_total=True, sort_order=SortOrder.CUSTOM)

    table_design = FrequencyTableDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_freq_table_no_col_pct_from_item.html',
        output_title='Frequency Table',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        include_column_percent=True,
        decimal_points=3,
    )
    table_design.make_output()

