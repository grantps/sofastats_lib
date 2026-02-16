import sqlite3 as sqlite

from sofastats.conf.main import DbeName, SortOrder
from sofastats.output.tables.cross_tab import CrossTabDesign
from sofastats.output.tables.freq import FrequencyTableDesign
from sofastats.output.tables.interfaces import Column, Metric, Row

from sofastats_examples.scripts.conf import (
    output_folder, people_csv_file_path, sort_orders_yaml_file_path, sqlite_demo_db_file_path)

def cross_tab_from_sqlite_db_filtered(sqlite_cur):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.VALUE))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    design = CrossTabDesign(
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
    return design

def cross_tab_from_sqlite_db(sqlite_cur):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.VALUE))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    design = CrossTabDesign(
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
    return design

def cross_tab(csv_file_path):
    """
    Top-level row variables (design settings and any nested variables)
    Top-level column variables (design settings and any nested variables)
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.VALUE))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
         child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    design = CrossTabDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_main_cross_tab.html',
        output_title='Cross Tab',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        style_name='red_spirals',
        decimal_points=2,
    )
    return design

def repeat_level_two_row_var_cross_tab(csv_file_path):
    """
    Repeated row level 2 was no issue BUT a bug in the col ordering
    """
    row_variables_design_1 = Row(variable_name='Country', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.VALUE))
    row_variables_design_2 = Row(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM,
        pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT])

    design = CrossTabDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_main_cross_tab_repeated_levels.html',
        output_title='Cross Tab (Repeated Levels)',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        column_variable_designs=[col_variables_design_1, ],
        style_name='gray_spirals',
        decimal_points=2,
        debug=False,
        verbose=False,
    )
    return design

def simple_freq_tbl(csv_file_path):
    row_variables_design_1 = Row(variable_name='Country', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Row(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM)

    design = FrequencyTableDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_freq_table_no_col_pct_from_item.html',
        output_title='Frequency Table',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        include_column_percent=True,
        decimal_points=3,
    )
    return design

def run():
    pass

    # con = sqlite.connect(sqlite_demo_db_file_path)
    # cur = con.cursor()
    # cross_tab_from_sqlite_db_filtered(cur).make_output()
    # cross_tab_from_sqlite_db(cur).make_output()
    # con.close()
    #
    # cross_tab(people_csv_file_path).make_output()
    # repeat_level_two_row_var_cross_tab(people_csv_file_path).make_output()
    # simple_freq_tbl(people_csv_file_path).make_output()

if __name__ == '__main__':
    run()
