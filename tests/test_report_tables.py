from functools import partial

from sofastats.conf.main import SortOrder
from sofastats.output.tables.cross_tab import CrossTabDesign
from sofastats.output.tables.freq import FrequencyTableDesign
from sofastats.output.tables.interfaces import Column, Metric, Row
from tests.conf import (
    handedness_custom_sorted, people_csv_fpath, sleep_groups_custom_sorted, sort_orders_yaml_file_path)
from tests.utils import (display_amount_as_nice_str, display_float_fraction_as_nice_pct_str,
    found_amount_sequence_in_html_table, sort_index_following_pattern)
import pandas as pd

def test_cross_tab():
    """
    Pick a couple of blocks and include some totals and some row and col percentages.
    """
    csv_file_path = people_csv_fpath
    row_variables_design_1 = Row(variable_name='Country', has_total=True,
        child=Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Home Location Type', has_total=True, sort_order=SortOrder.CUSTOM)
    row_variables_design_3 = Row(variable_name='Car')

    col_variables_design_1 = Column(variable_name='Sleep Group', has_total=True, sort_order=SortOrder.CUSTOM)
    col_variables_design_2 = Column(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM,
        child=Column(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM, pct_metrics=[Metric.ROW_PCT, Metric.COL_PCT]))
    col_variables_design_3 = Column(variable_name='Tertiary Qualifications', has_total=True, sort_order=SortOrder.CUSTOM)

    decimal_points = 7

    design = CrossTabDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, row_variables_design_3],
        column_variable_designs=[col_variables_design_1, col_variables_design_2, col_variables_design_3],
        decimal_points=decimal_points,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    table_html = html[html.index('<table'):]  ## e.g. <table id="T_02ac2">
    found_amount_sequence = partial(found_amount_sequence_in_html_table, text=table_html, debug=True)
    ## Frequencies - Country > Home Location Type vs Sleep Group
    s_denmark_city_by_sleep_group_freqs = (
        df.loc[(df['Country'] == 'Denmark') & (df['Home Location Type'] == 'City'), ['Sleep Group']]
        .groupby('Sleep Group').size())
    sort_by_sleep_group = partial(sort_index_following_pattern, sorted_items_providing_pattern=sleep_groups_custom_sorted)
    denmark_city_sleep_group_freqs = s_denmark_city_by_sleep_group_freqs.sort_index(key=sort_by_sleep_group).tolist()
    denmark_city_sleep_group_freqs += [sum(denmark_city_sleep_group_freqs)]  ## include total column
    assert found_amount_sequence(vals2find=denmark_city_sleep_group_freqs)
    ## Freq and Pcts - Home Location Type vs Age Group > Handedness
    ## Freq
    sort_by_handedness = partial(sort_index_following_pattern, sorted_items_providing_pattern=handedness_custom_sorted)
    s_city_under_20_by_handedness_freqs = (
        df.loc[(df['Home Location Type'] == 'City') & (df['Age Group'] == '<20'), ['Handedness']]
        .groupby('Handedness').size())
    city_under_20_by_handedness_freqs = s_city_under_20_by_handedness_freqs.sort_index(key=sort_by_handedness).tolist()
    ## Percents
    s_under_20_by_handedness_col_totals = df.loc[df['Age Group'] == '<20', ['Handedness']].groupby('Handedness').size()
    under_20_by_handedness_col_totals = s_under_20_by_handedness_col_totals.sort_index(key=sort_by_handedness).tolist()
    ## for each freq, add in row then column percentage
    amounts = []
    row_total = sum(city_under_20_by_handedness_freqs)
    col_total = sum(under_20_by_handedness_col_totals)
    for handedness_freq, handedness_col_total in zip(city_under_20_by_handedness_freqs, under_20_by_handedness_col_totals):
        amounts.append(handedness_freq)
        amounts.append(display_float_fraction_as_nice_pct_str(float_fraction=handedness_freq / row_total,
            decimal_points=decimal_points))
        amounts.append(display_float_fraction_as_nice_pct_str(float_fraction=handedness_freq / handedness_col_total,
            decimal_points=decimal_points))
    amounts.append(row_total)
    amounts.append(display_amount_as_nice_str(100.0, decimal_points=decimal_points))
    amounts.append(display_float_fraction_as_nice_pct_str(float_fraction=row_total / col_total,
        decimal_points=decimal_points))
    assert found_amount_sequence(vals2find=amounts)

def test_simple_freq_table():

    csv_file_path = people_csv_fpath
    row_variables_design_1 = Row(variable_name='Country', has_total=True,
        child=Row(variable_name='Handedness', has_total=True, sort_order=SortOrder.CUSTOM))
    row_variables_design_2 = Row(variable_name='Age Group', has_total=True, sort_order=SortOrder.CUSTOM)
    decimal_points = 3

    design = FrequencyTableDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        row_variable_designs=[row_variables_design_1, row_variables_design_2, ],
        include_column_percent=True,
        decimal_points=decimal_points,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    table_html = html[html.index('<table'):]  ## e.g. <table id="T_02ac2">
    found_amount_sequence = partial(found_amount_sequence_in_html_table, text=table_html, debug=True)
    ## Frequencies Country > Handedness - Freq and Col%
    s_nz_by_handedness_freqs = df.loc[df['Country'] == 'NZ', ['Handedness']].groupby('Handedness').size()
    sort_by_handedness = partial(sort_index_following_pattern, sorted_items_providing_pattern=handedness_custom_sorted)
    nz_by_handedness_freqs = s_nz_by_handedness_freqs.sort_index(key=sort_by_handedness).tolist()
    col_total = sum(nz_by_handedness_freqs)
    freq_amounts = nz_by_handedness_freqs + [col_total, ]
    col_pct_amounts = [
        display_float_fraction_as_nice_pct_str(float_fraction=freq / col_total, decimal_points=decimal_points)
        for freq in freq_amounts]
    ## freq and col % are interleaved
    amounts = []
    for paired_amounts in zip(freq_amounts, col_pct_amounts):
        amounts.extend(paired_amounts)
    assert found_amount_sequence(vals2find=amounts)

if __name__ == "__main__":
    pass
    # test_cross_tab()
    # test_simple_freq_table()
