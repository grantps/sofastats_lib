from collections.abc import Sequence

from sofastats.conf.main import SortOrder
from sofastats.output.charts.bar import (
    ClusteredBarChartDesign, MultiChartBarChartDesign, MultiChartClusteredBarChartDesign, SimpleBarChartDesign)
from sofastats.output.charts.box_plot import BoxplotChartDesign, ClusteredBoxplotChartDesign
from sofastats.stats_calc.interfaces import BoxplotType

from tests.conf import (age_groups_sorted, age_groups_unsorted, countries_sorted,
    handedness_sorted, home_location_types_sorted,
    people_csv_fpath, sort_orders_yaml_file_path)

def check_category_order(*, html: str, category_values_in_expected_order: Sequence[str]):
    for n, category in enumerate(category_values_in_expected_order, 1):
        assert f'{{value: {n}, text: "{category}"}}' in html

def test_simple_bar_chart_unsorted():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_unsorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        category_field_name=category_field_name,
    )
    html = design.to_html_design().html_item_str
    # print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)

def test_simple_bar_chart_sorted():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    # print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)

def test_multi_chart_bar_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    chart_field_name = 'Country'
    design = MultiChartBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name=chart_field_name,
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    # print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)
    ## TODO: check chart order

def test_clustered_bar_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    series_field_name = 'Country'
    design = ClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        series_field_name=series_field_name,
        series_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    # print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)
    ## TODO: check series order

def test_multi_chart_clustered_bar_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    series_field_name = 'Country'
    chart_field_name = 'Tertiary Qualifications'
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        series_field_name=series_field_name,
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name=chart_field_name,
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    # print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)
    ## TODO: check chart order and series order

def test_box_plot():
    """
    Only checking median and quartile ranges (both trusted external code)

    summary_data_00_0['box_bottom'] = 26;
    summary_data_00_0['box_bottom_rounded'] = 26;
    summary_data_00_0['median'] = 45.0;
    summary_data_00_0['median_rounded'] = 45.0;
    summary_data_00_0['box_top'] = 66;
    summary_data_00_0['box_top_rounded'] = 66;
    """
    csv_file_path = people_csv_fpath
    field_name = 'Age'
    category_field_name = 'Handedness'
    category_values_in_expected_order = handedness_sorted
    design = BoxplotChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        field_name=field_name,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    html = design.to_html_design().html_item_str
    print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)

def test_clustered_box_plot():
    csv_file_path = people_csv_fpath
    field_name = 'Age'
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    series_field_name = 'Country'
    series_values_in_expected_order = countries_sorted
    design = ClusteredBoxplotChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        field_name=field_name,
        category_field_name=category_field_name,
        series_field_name=series_field_name,
        series_sort_order=SortOrder.CUSTOM,
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    html = design.to_html_design().html_item_str
    print(html)
    check_category_order(html=html, category_values_in_expected_order=category_values_in_expected_order)

if __name__ == '__main__':
    pass
    # test_simple_bar_chart_unsorted()
    # test_simple_bar_chart_sorted()
    # test_multi_chart_bar_chart()
    # test_clustered_bar_chart()
    # test_multi_chart_clustered_bar_chart()
    # test_box_plot()
    # test_clustered_box_plot()
