"""
Strategy for getting sorted category items (values or labels)

1. Get a starting df from which to calculate category values.
   If inside a loop (chart values or series values), or loops (chart and series values) filter accordingly.
   E.g. if charts by Country and category is Age Group we start by df_vals = df.loc[df['Country'] == country]
   E.g. if charts by Country, series by Home Location Type, and category is Age Group we start by
   df_filtered = df.loc[(df['Country'] == country) & (df['Home Location Type'] == home_location_type)]

2. Rely on pandas .groupby() to do the hard work of getting all category values per group at once.
   For category frequencies, s_freqs = df_filtered.groupby(<category_field_name>).size()
   For category percentages, s_pcts = ((100 * df_filtered.groupby(<category_field_name>).size()) / len(df_filtered))
   For category averages, s_avgs = df_filtered.groupby(<category_field_name>)[<field_name>].mean()
   For category sums, s_sums = df_filtered.groupby(<category_field_name>)[<field_name>].sum()

3. Convert resulting series into dictionaries so we can pluck values out using keys we supply following a sort order
   we control externally. E.g. looping through sorted or value_sorted Age Group values.
   category2freq = dict(s_freqs.items())
   category2pct = dict(s_pcts.items())

4. Gather category values and labels into lists e.g.
   category_freqs = []
   category_labels = []
   for category in age_groups_value_sorted:
       ## use dictionary to extract value for specified category
       category_freq = category2freq[category]
       category_freqs.append(category_freq)
       category_pct = display_pcts(category2pct[category])
       category_label = f"'{category_freq}<br>({category_pct}%)'"
       category_labels.append(category_label)

5. Assemble expected HTML content from lists
   I.e. "vals=[...]"; "yLbls: [...]" with individual items generated from f-strings
   such as f"{freq}<br>({label}%)" when no series
   or f"{<category_name>}, {<series_name>}<br>{freq}<br>({label}%)" when a series variable
"""
## TODO: expected sort order - how to handle allowed missing items
## continue from multi-chart pie chart onwards

from collections.abc import Sequence
from statistics import median

import pandas as pd

from sofastats.conf.main import ChartMetric, SortOrder
from sofastats.output.charts.area import AreaChartDesign, MultiChartAreaChartDesign
from sofastats.output.charts.bar import (
    ClusteredBarChartDesign, MultiChartBarChartDesign, MultiChartClusteredBarChartDesign, SimpleBarChartDesign)
from sofastats.output.charts.box_plot import BoxplotChartDesign, ClusteredBoxplotChartDesign
from sofastats.output.charts.histogram import HistogramChartDesign, MultiChartHistogramChartDesign
from sofastats.output.charts.line import (
    LineChartDesign, MultiChartLineChartDesign, MultiChartMultiLineChartDesign, MultiLineChartDesign)
from sofastats.output.charts.pie import MultiChartPieChartDesign, PieChartDesign
from sofastats.output.charts.scatter_plot import (BySeriesScatterChartDesign, MultiChartBySeriesScatterChartDesign,
    MultiChartScatterChartDesign, SimpleScatterChartDesign)
from sofastats.stats_calc.interfaces import BoxplotType
from sofastats.utils.item_sorting import sort_values_by_value_or_custom_if_possible
from sofastats.utils.stats import get_quartiles

from tests.conf import (age_groups_custom_sorted, age_groups_value_sorted,
    countries_custom_sorted, countries_value_sorted, education_csv_fpath,
    handedness_custom_sorted, handedness_value_sorted,
    home_location_types_custom_sorted, home_location_types_value_sorted,
    people_csv_fpath, sort_orders_yaml_file_path, sports_csv_file_path, sports_custom_sorted, sports_value_sorted)
from tests.utils import display_amount_as_nice_str, display_pct_as_nice_str

## common checks *******************************************************************************************************

def _check_n_records(
        *, df_filtered: pd.DataFrame, html: str, series_value: str | None = None, already_checked_n_records=False):
    if series_value:  ## if by series then have to do n_record calculations out at the chart / total df level
        if not already_checked_n_records:
            raise Exception("The n_records value needs to be checked but this has to happen outside of "
                "the check_category_freqs() function call when there is a series "
                "because we don't have access to the full df")
    else:
        n_records = len(df_filtered)
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records

def _initial_category_checks(*, df_filtered: pd.DataFrame, html: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, already_checked_n_records=False):
    """
    Note - frequencies by category have % in labels so some shared logic with percentages by category
    Some things are in common between area, bar, and line.

    If by chart only - Category, Chart ...
    If by series only - Category, Series ...
    If by chart AND series - Category, Series ...
    """
    _check_n_records(df_filtered=df_filtered, html=html, series_value=series_value,
        already_checked_n_records=already_checked_n_records)
    for n, category in enumerate(category_values_in_expected_order, 1):
        category_label = f'{{value: {n}, text: "{category}"}}'
        assert category_label in html, category_label

def check_category_freqs(*, df_filtered: pd.DataFrame, html: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, chart_value: str | None = None, already_checked_n_records=False,
        decimal_points: int = 3):
    _initial_category_checks(df_filtered=df_filtered, html=html,
        category_values_in_expected_order=category_values_in_expected_order,
        series_value=series_value, already_checked_n_records=already_checked_n_records)
    s_freqs = df_filtered.groupby(category_field_name).size()
    s_pcts = ((100 * df_filtered.groupby(category_field_name).size()) / len(df_filtered))
    category2freq = dict(s_freqs.items())
    category2pct = dict(s_pcts.items())
    category_freqs = []
    category_labels = []
    for category in category_values_in_expected_order:
        category_freq = category2freq[category]
        category_freqs.append(category_freq)
        category_pct = category2pct[category]
        if series_value is not None:
            filter_lbl = f"{category}, {series_value}<br>"
        elif chart_value is not None:
            filter_lbl = f"{category}, {chart_value}<br>"
        else:
            filter_lbl = ''
        label_pct = display_pct_as_nice_str(category_pct, decimal_points=decimal_points)
        category_label = f"'{filter_lbl}{category_freq}<br>({label_pct})'"
        category_labels.append(category_label)
    vals = f'["vals"] = {category_freqs};'
    assert vals in html, vals
    y_labels = "yLbls: [" + ", ".join(category_labels) + "]"
    assert y_labels in html, y_labels

def check_category_pcts(*, df_filtered: pd.DataFrame, html: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, chart_value: str | None = None, already_checked_n_records=False,
        decimal_points: int = 3):
    """
    Note - frequencies by category have % in labels so some shared logic with percentages by category
    Some things are in common between area, bar, and line.
    """
    _initial_category_checks(df_filtered=df_filtered, html=html,
        category_values_in_expected_order=category_values_in_expected_order,
        series_value=series_value, already_checked_n_records=already_checked_n_records)
    s_freqs = df_filtered.groupby(category_field_name).size()
    s_pcts = ((100 * df_filtered.groupby(category_field_name).size()) / len(df_filtered))
    category2freq = dict(s_freqs.items())
    category2pct = dict(s_pcts.items())
    category_pcts = []  ## raw values with all decimal points so graph accurate
    category_labels = []  ## rounded values so sensible to read
    for category in category_values_in_expected_order:
        category_freq = category2freq[category]
        category_pct = category2pct[category]
        category_pcts.append(category_pct)
        if series_value is not None:
            filter_lbl = f"{category}, {series_value}<br>"
        elif chart_value is not None:
            filter_lbl = f"{category}, {chart_value}<br>"
        else:
            filter_lbl = ''
        label_pct = display_pct_as_nice_str(category_pct, decimal_points=decimal_points)
        category_label = f"'{filter_lbl}{category_freq}<br>({label_pct})'"
        category_labels.append(category_label)
    vals = f'["vals"] = {category_pcts};'
    assert vals in html, vals
    y_labels = "yLbls: [" + ", ".join(category_labels) + "]"
    assert y_labels in html, y_labels

def check_category_averages(*, df_filtered: pd.DataFrame, html: str, field_name: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str], decimal_points: int = 3):
    """
    Values are unrounded averages; labels are rounded
    """
    n_records = len(df_filtered)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    for n, category in enumerate(category_values_in_expected_order, 1):
        assert f'{{value: {n}, text: "{category}"}}' in html
    s_avgs = df_filtered.groupby(category_field_name)[field_name].mean()
    category2avg = dict(s_avgs.items())
    category_avgs = []  ## raw values with all decimal points so graph accurate
    category_labels = []  ## rounded values so sensible to read
    for category in category_values_in_expected_order:
        category_avg = category2avg[category]
        category_avgs.append(category_avg)
        category_label = f"'{display_amount_as_nice_str(category_avg, decimal_points=decimal_points)}'"
        category_labels.append(category_label)
    vals = f'["vals"] = {category_avgs};'
    assert vals in html, vals
    y_labels = "yLbls: [" + ", ".join(category_labels) + "]"
    assert y_labels in html, y_labels

def check_category_sums(*, df_filtered: pd.DataFrame, html: str, field_name: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str], decimal_points: int = 3):
    """
    Values are unrounded averages; labels are rounded
    """
    n_records = len(df_filtered)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    for n, category in enumerate(category_values_in_expected_order, 1):
        assert f'{{value: {n}, text: "{category}"}}' in html
    s_sums = df_filtered.groupby(category_field_name)[field_name].sum()
    category2sum = dict(s_sums.items())
    category_sums = []  ## raw values with all decimal points so graph accurate
    category_labels = []  ## rounded values so sensible to read
    for category in category_values_in_expected_order:
        category_sum = category2sum[category]
        category_sums.append(category_sum)
        category_label = f"'{display_amount_as_nice_str(category_sum, decimal_points=decimal_points)}'"
        category_labels.append(category_label)
    vals = f'["vals"] = {category_sums};'
    assert vals in html, vals
    y_labels = "yLbls: [" + ", ".join(category_labels) + "]"
    assert y_labels in html, y_labels

def check_category_slices(*, df_filtered: pd.DataFrame, html: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, chart_value: str | None = None):
    """
    {"val": 2227, "label": "USA", "tool_tip": "2227<br>(44.54%)"},
    {"val": 897, "label": "NZ", "tool_tip": "897<br>(17.94%)"},
    {"val": 1140, "label": "South Korea", "tool_tip": "1140<br>(22.8%)"},
    {"val": 736, "label": "Denmark", "tool_tip": "736<br>(14.72%)"}
    """
    n_records = len(df_filtered)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    s_freqs = df_filtered.groupby(category_field_name).size()
    s_pcts = ((100 * df_filtered.groupby(category_field_name).size()) / len(df_filtered))
    category2freq = dict(s_freqs.items())
    category2pct = dict(s_pcts.items())
    html_shrinking = html
    for category in category_values_in_expected_order:
        category_freq = category2freq[category]
        category_pct = category2pct[category]
        if series_value is not None:
            filter_lbl = f"{category}, {series_value}<br>"
        elif chart_value is not None:
            filter_lbl = f"{category}, {chart_value}<br>"
        else:
            filter_lbl = ''
        category_slice = (f'{{"val": {category_freq}, "label": "{category}", '
            f'"tool_tip": "{filter_lbl}{category_freq}<br>({display_pct_as_nice_str(category_pct)})"}}')
        assert category_slice in html_shrinking, category_slice
        html_shrinking = html_shrinking[html_shrinking.index(category_slice):]

def check_some_points(*, df_filtered: pd.DataFrame, html: str,
        x_field_name: str, y_field_name: str,
        series_value: str | None = None, already_checked_n_records=False):
    _check_n_records(df_filtered=df_filtered, html=html, series_value=series_value,
        already_checked_n_records=already_checked_n_records)
    df_points = df_filtered.groupby([x_field_name, y_field_name]).size().reset_index()
    sane_n_points_to_check = 100
    idx: int
    for idx, row in df_points.iterrows():
        point_defn = f"{{x: {row[x_field_name]}, y: {row[y_field_name]}}}"
        assert point_defn in html, point_defn
        if idx + 1 == sane_n_points_to_check:
            break

def check_bins(*, df_filtered: pd.DataFrame, html: str, field_name: str):
    n_records = len(df_filtered)  ## filter to chart
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    bin_ranges = [(5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 35), (35, 40), (40, 45), (45, 50), (50, 55),
        (55, 60), (60, 65), (65, 70), (70, 75), (75, 80), (80, 85), (85, 90), (90, 95),
        (95, 100),  ## <= instead of the usual <
    ]
    vals = []
    for n, (bin_start, bin_end) in enumerate(bin_ranges, 1):
        last_bin = (n == len(bin_ranges))
        if last_bin:
            df_freq = df_filtered.loc[(df_filtered[field_name] >= bin_start) & (df_filtered[field_name] <= bin_end)]  ## inclusive end
        else:
            df_freq = df_filtered.loc[(df_filtered[field_name] >= bin_start) & (df_filtered[field_name] < bin_end)]
        val = len(df_freq)
        vals.append(val)
    y_vals = f'data_spec["y_vals"] = {vals}'
    assert y_vals in html, y_vals

def check_boxes(*, df_filtered: pd.DataFrame, html: str, category_field_name: str, field_name: str,
        category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, series_idx: int = 0, chart_value: str | None = None,
        already_checked_n_records=False):
    _check_n_records(df_filtered=df_filtered, html=html, series_value=series_value,
        already_checked_n_records=already_checked_n_records)
    for i, category_value in enumerate(category_values_in_expected_order):
        if series_value is not None:
            filter_lbl = f"{category_value}, {series_value}"
        elif chart_value is not None:
            filter_lbl = f"{category_value}, {chart_value}"
        else:
            filter_lbl = category_value
        category_label = f"""box_{series_idx:02}_{i}['indiv_boxlbl'] = "{filter_lbl}";"""
        assert category_label in html, category_label
        vals = df_filtered.loc[df_filtered[category_field_name] == category_value, field_name].values.tolist()
        ## calculate quartiles, median etc
        lower_quartile, upper_quartile = get_quartiles(vals)
        box_bottom = lower_quartile
        bottom = f"['box_bottom'] = {box_bottom};"
        assert bottom in html, bottom
        box_top = upper_quartile
        top = f"['box_top'] = {box_top};"
        assert top in html, top
        box_median = median(vals)
        med = f"['median'] = {box_median};"
        assert med in html, med

## tests ***************************************************************************************************************

def test_simple_bar_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)

def test_simple_bar_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)


def test_simple_bar_chart_percents_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        metric=ChartMetric.PCT,
        category_field_name='Age Group',
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_pcts(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)

def test_simple_bar_chart_percents_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.PCT,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_pcts(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)


def test_simple_bar_chart_averages_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        metric=ChartMetric.AVG,
        field_name='Sleep',
        category_field_name='Age Group',
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_averages(df_filtered=df, html=html, field_name=design.field_name,
        category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)

def test_simple_bar_chart_averages_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.AVG,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_averages(df_filtered=df, html=html, field_name=design.field_name,
        category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)


def test_simple_bar_chart_sums_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        metric=ChartMetric.SUM,
        field_name='Sleep',
        category_field_name='Age Group',
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_sums(df_filtered=df, html=html, field_name=design.field_name,
        category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)

def test_simple_bar_chart_sums_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.SUM,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_sums(df_filtered=df, html=html, field_name=design.field_name,
        category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)


def test_multi_chart_bar_chart_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Home Location Type',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_multi_chart_bar_chart_category_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Home Location Type',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_multi_chart_bar_chart_charts_value_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_multi_chart_bar_chart_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)


def test_clustered_bar_chart_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = ClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Home Location Type',
        series_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## when no chart, but series, have to do it here
    record = f'conf["n_records"] = "N = {n_records:,}";'
    assert record in html, record
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_clustered_bar_chart_category_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = ClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## when no chart, but series, have to do it here
    record = f'conf["n_records"] = "N = {n_records:,}";'
    assert record in html, record
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_clustered_bar_chart_series_value_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = ClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## when no chart, but series, have to do it here
    record = f'conf["n_records"] = "N = {n_records:,}";'
    assert record in html, record
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_clustered_bar_chart_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = ClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## when no chart, but series, have to do it here
    record = f'conf["n_records"] = "N = {n_records:,}";'
    assert record in html, record
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)


def test_multi_chart_clustered_bar_chart_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Home Location Type',
        series_field_name='Country',
        chart_field_name='Tertiary Qualifications',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        value_sorted_series_values = sorted(series_values)
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_category_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_series_value_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        value_sorted_series_values = sorted(series_values)
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_chart_value_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_category_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        chart_field_name='Tertiary Qualifications',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        value_sorted_series_values = sorted(series_values)
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_series_custom_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_bar_chart_charts_custom_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        series_field_name='Country',
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        value_sorted_series_values = sorted(series_values)
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label  ## series
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)


def test_multi_chart_clustered_percents_bar_chart_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.PCT,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Tertiary Qualifications',
        chart_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_pcts(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True, decimal_points=design.decimal_points)


def test_line_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = LineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)

def test_line_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = LineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)


def test_multi_line_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = MultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
        series_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_multi_line_chart_category_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = MultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_multi_line_chart_series_value_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = MultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_multi_line_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = MultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)


def test_multi_chart_line_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = MultiChartLineChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            chart_value=chart_value, already_checked_n_records=True)

def test_multi_chart_line_chart_charts_value_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = MultiChartLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            chart_value=chart_value, already_checked_n_records=True)

def test_multi_chart_line_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = MultiChartLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            chart_value=chart_value, already_checked_n_records=True)






def test_multi_chart_multi_line_chart_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = MultiChartMultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Home Location Type',
        series_field_name='Country',
        chart_field_name='Age Group',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        value_sorted_series_values = sorted(series_values)
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_multi_line_chart_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    design = MultiChartMultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Age Group',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)


def test_area_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = AreaChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)

def test_area_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = AreaChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_freqs(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order, decimal_points=design.decimal_points)


def test_multi_chart_area_chart_value_sorted():
    category_values_in_expected_order = age_groups_value_sorted
    design = MultiChartAreaChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_multi_chart_area_chart_custom_sorted():
    category_values_in_expected_order = age_groups_custom_sorted
    design = MultiChartAreaChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)


def test_pie_chart_value_sorted():
    category_values_in_expected_order = countries_value_sorted
    design = PieChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_slices(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)

def test_pie_chart_custom_sorted():
    category_values_in_expected_order = countries_custom_sorted
    design = PieChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Country',
        category_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_category_slices(df_filtered=df, html=html, category_field_name=design.category_field_name,
        category_values_in_expected_order=category_values_in_expected_order)


def test_multi_chart_pie_chart_value_sorted():
    category_values_in_expected_order = sports_value_sorted
    design = MultiChartPieChartDesign(
        csv_file_path=sports_csv_file_path,
        category_field_name='Sport',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_slices(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_multi_chart_pie_chart_custom_sorted():
    category_values_in_expected_order = sports_custom_sorted
    design = MultiChartPieChartDesign(
        csv_file_path=sports_csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Sport',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_category_slices(df_filtered=df_filtered, html=html, category_field_name=design.category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)


def test_simple_scatter_plot():
    design = SimpleScatterChartDesign(
        csv_file_path=education_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_some_points(df_filtered=df, html=html, x_field_name=design.x_field_name, y_field_name=design.y_field_name)


def test_by_series_scatter_plot_value_sorted():
    design = BySeriesScatterChartDesign(
        csv_file_path=education_csv_fpath,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_some_points(df_filtered=df_filtered, html=html,
            x_field_name=design.x_field_name, y_field_name=design.y_field_name,
            series_value=series_value, already_checked_n_records=True)

def test_by_series_scatter_plot_custom_sorted():
    design = BySeriesScatterChartDesign(
        csv_file_path=education_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
        assert series_label in html, series_label
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_some_points(df_filtered=df_filtered, html=html,
            x_field_name=design.x_field_name, y_field_name=design.y_field_name,
            series_value=series_value, already_checked_n_records=True)


def test_multi_chart_scatter_plot_value_sorted():
    design = MultiChartScatterChartDesign(
        csv_file_path=education_csv_fpath,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html  ## so test will fail if chart labels not in the correct order
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_some_points(df_filtered=df_filtered, html=html,
            x_field_name=design.x_field_name, y_field_name=design.y_field_name)

def test_multi_chart_scatter_plot_custom_sorted():
    design = MultiChartScatterChartDesign(
        csv_file_path=education_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html  ## so test will fail if chart labels not in the correct order
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_some_points(df_filtered=df_filtered, html=html,
            x_field_name=design.x_field_name, y_field_name=design.y_field_name)


def test_multi_chart_by_series_scatter_plot_value_sorted():
    design = MultiChartBySeriesScatterChartDesign(
        csv_file_path=education_csv_fpath,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Home Location Type',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        value_sorted_series_values = sorted(series_values)
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        for series_idx, series_value in enumerate(value_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_some_points(df_filtered=df_filtered, html=html,
                x_field_name=design.x_field_name, y_field_name=design.y_field_name,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_by_series_scatter_plot_custom_sorted():
    design = MultiChartBySeriesScatterChartDesign(
        csv_file_path=education_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        x_field_name='Reading Score Before Help',
        y_field_name='Reading Score After Help',
        series_field_name='Home Location Type',
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        series_values = df[design.series_field_name].unique()
        custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
            values=series_values, sort_orders=design.sort_orders, sort_order=design.series_sort_order)
        df_chart = df[df[design.chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        records = f'conf["n_records"] = "N = {n_records:,}";'
        assert records in html, records
        for series_idx, series_value in enumerate(custom_sorted_series_values):
            series_label = f'series_{series_idx:>02}["label"] = "{series_value}"'
            assert series_label in html, series_label
            df_filtered = df.loc[
                (df[design.chart_field_name] == chart_value) & (df[design.series_field_name] == series_value)]
            check_some_points(df_filtered=df_filtered, html=html,
                x_field_name=design.x_field_name, y_field_name=design.y_field_name,
                series_value=series_value, already_checked_n_records=True)


def test_histogram():
    """
    Hard to make the test easier to trust than the code so supply the expected bins and calculate totals within them.
    Don't do the normal curve as well. Labels are in the JS so can't check in HTML.
    """
    design = HistogramChartDesign(
        csv_file_path=people_csv_fpath,
        field_name='Age',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_bins(df_filtered=df, html=html, field_name=design.field_name)


def test_multi_chart_histogram_value_sorted():
    design = MultiChartHistogramChartDesign(
        csv_file_path=people_csv_fpath,
        field_name='Age',
        chart_field_name='Country',
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    value_sorted_chart_values = sorted(chart_values)
    html_shrinking = html
    for chart_value in value_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_bins(df_filtered=df_filtered, html=html, field_name=design.field_name)

def test_multi_chart_histogram_custom_sorted():
    design = MultiChartHistogramChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        field_name='Age',
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    chart_values = df[design.chart_field_name].unique()
    custom_sorted_chart_values = sort_values_by_value_or_custom_if_possible(variable_name=design.chart_field_name,
        values=chart_values, sort_orders=design.sort_orders, sort_order=design.chart_sort_order)
    html_shrinking = html
    for chart_value in custom_sorted_chart_values:
        chart_label = f"{design.chart_field_name}: {chart_value}"
        assert chart_label in html_shrinking, chart_label
        html_shrinking = html[html.index(chart_label):]
        df_filtered = df.loc[df[design.chart_field_name] == chart_value]
        check_bins(df_filtered=df_filtered, html=html, field_name=design.field_name)


def test_box_plot_value_sorted():
    """
    Only checking median and quartile ranges (both trusted external code)

    summary_data_00_0['box_bottom'] = 26;
    summary_data_00_0['box_bottom_rounded'] = 26;
    summary_data_00_0['median'] = 45.0;
    summary_data_00_0['median_rounded'] = 45.0;
    summary_data_00_0['box_top'] = 66;
    summary_data_00_0['box_top_rounded'] = 66;
    """
    category_values_in_expected_order = handedness_value_sorted
    design = BoxplotChartDesign(
        csv_file_path=people_csv_fpath,
        field_name='Age',
        category_field_name='Handedness',
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_boxes(df_filtered=df, html=html, category_field_name=design.category_field_name, field_name=design.field_name,
        category_values_in_expected_order=category_values_in_expected_order)

def test_box_plot_custom_sorted():
    """
    Only checking median and quartile ranges (both trusted external code)

    summary_data_00_0['box_bottom'] = 26;
    summary_data_00_0['box_bottom_rounded'] = 26;
    summary_data_00_0['median'] = 45.0;
    summary_data_00_0['median_rounded'] = 45.0;
    summary_data_00_0['box_top'] = 66;
    summary_data_00_0['box_top_rounded'] = 66;
    """
    category_values_in_expected_order = handedness_custom_sorted
    design = BoxplotChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        field_name='Age',
        category_field_name='Handedness',
        category_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    check_boxes(df_filtered=df, html=html, category_field_name=design.category_field_name, field_name=design.field_name,
        category_values_in_expected_order=category_values_in_expected_order)


def test_clustered_box_plot_value_sorted():
    category_values_in_expected_order = home_location_types_value_sorted
    design = ClusteredBoxplotChartDesign(
        csv_file_path=people_csv_fpath,
        field_name='Age',
        category_field_name='Home Location Type',
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## filter to chart
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    value_sorted_series_values = sorted(series_values)
    for series_idx, series_value in enumerate(value_sorted_series_values):
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_boxes(df_filtered=df_filtered, html=html,
            category_field_name=design.category_field_name, field_name=design.field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, series_idx=series_idx, already_checked_n_records=True)

def test_clustered_box_plot_custom_sorted():
    category_values_in_expected_order = home_location_types_custom_sorted
    series_sort_order = SortOrder.CUSTOM
    design = ClusteredBoxplotChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        field_name='Age',
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=series_sort_order,
        box_plot_type=BoxplotType.INSIDE_1_POINT_5_TIMES_IQR,
    )
    # design.make_output()
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(design.csv_file_path)
    n_records = len(df)  ## filter to chart
    records = f'conf["n_records"] = "N = {n_records:,}";'
    assert records in html, records
    series_values = df[design.series_field_name].unique()
    custom_sorted_series_values = sort_values_by_value_or_custom_if_possible(variable_name=design.series_field_name,
        values=series_values, sort_orders=design.sort_orders, sort_order=series_sort_order)
    for series_idx, series_value in enumerate(custom_sorted_series_values):
        df_filtered = df.loc[df[design.series_field_name] == series_value]
        check_boxes(df_filtered=df_filtered, html=html,
            category_field_name=design.category_field_name, field_name=design.field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, series_idx=series_idx, already_checked_n_records=True)

if __name__ == "__main__":
    pass

    test_simple_bar_chart_value_sorted()
    test_simple_bar_chart_custom_sorted()

    test_simple_bar_chart_percents_value_sorted()
    test_simple_bar_chart_percents_custom_sorted()

    test_simple_bar_chart_averages_value_sorted()
    test_simple_bar_chart_averages_custom_sorted()

    test_simple_bar_chart_sums_value_sorted()
    test_simple_bar_chart_sums_custom_sorted()

    test_multi_chart_bar_chart_value_sorted()
    test_multi_chart_bar_chart_category_value_sorted()
    test_multi_chart_bar_chart_charts_value_sorted()
    test_multi_chart_bar_chart_custom_sorted()

    test_clustered_bar_chart_value_sorted()
    test_clustered_bar_chart_category_value_sorted()
    test_clustered_bar_chart_series_value_sorted()
    test_clustered_bar_chart_custom_sorted()

    test_multi_chart_clustered_bar_chart_value_sorted()
    test_multi_chart_clustered_bar_chart_category_value_sorted()
    test_multi_chart_clustered_bar_chart_series_value_sorted()
    test_multi_chart_clustered_bar_chart_chart_value_sorted()
    test_multi_chart_clustered_bar_chart_category_custom_sorted()
    test_multi_chart_clustered_bar_chart_series_custom_sorted()
    test_multi_chart_clustered_bar_chart_charts_custom_sorted()
    test_multi_chart_clustered_bar_chart_custom_sorted()

    test_multi_chart_clustered_percents_bar_chart_custom_sorted()  ## not doing all the variants of percents as well - already more than adequately tested under bar frequency testing

    test_line_chart_value_sorted()
    test_line_chart_custom_sorted()

    test_multi_line_chart_value_sorted()  ## not doing all the variants of lines - already more than adequately tested under bar frequency testing (bar, area, and line all use same code underneath)
    test_multi_line_chart_category_value_sorted()
    test_multi_line_chart_series_value_sorted()
    test_multi_line_chart_custom_sorted()

    test_multi_chart_line_chart_value_sorted()
    test_multi_chart_line_chart_charts_value_sorted()
    test_multi_chart_line_chart_custom_sorted()

    test_multi_chart_multi_line_chart_value_sorted()  ## not doing all the variants of this as well - already more than adequately tested
    test_multi_chart_multi_line_chart_custom_sorted()

    test_area_chart_value_sorted()  ## not doing all the variants of area - already more than adequately tested under bar frequency testing (bar, area, and line all use same code underneath)
    test_area_chart_custom_sorted()

    test_multi_chart_area_chart_value_sorted()
    test_multi_chart_area_chart_custom_sorted()

    test_pie_chart_value_sorted()
    test_pie_chart_custom_sorted()

    test_multi_chart_pie_chart_value_sorted()
    test_multi_chart_pie_chart_custom_sorted()

    test_simple_scatter_plot()

    test_by_series_scatter_plot_value_sorted()
    test_by_series_scatter_plot_custom_sorted()

    test_multi_chart_scatter_plot_value_sorted()
    test_multi_chart_scatter_plot_custom_sorted()

    test_multi_chart_by_series_scatter_plot_value_sorted()
    test_multi_chart_by_series_scatter_plot_custom_sorted()

    test_histogram()

    test_multi_chart_histogram_value_sorted()
    test_multi_chart_histogram_custom_sorted()

    test_box_plot_value_sorted()
    test_box_plot_custom_sorted()

    test_clustered_box_plot_value_sorted()
    test_clustered_box_plot_custom_sorted()
