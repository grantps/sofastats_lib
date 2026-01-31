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
   we control externally. E.g. looping through sorted or unsorted Age Group values.
   category2freq = dict(s_freqs.items())
   category2pct = dict(s_pcts.items())

4. Gather category values and labels into lists e.g.
   category_freqs = []
   category_labels = []
   for category in age_groups_unsorted:
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
from collections.abc import Sequence
from pathlib import Path

from sofastats.conf.main import ChartMetric, SortOrder
from sofastats.output.charts.area import AreaChartDesign, MultiChartAreaChartDesign
from sofastats.output.charts.bar import (
    ClusteredBarChartDesign, MultiChartBarChartDesign, MultiChartClusteredBarChartDesign, SimpleBarChartDesign)
from sofastats.output.charts.line import (
    LineChartDesign, MultiChartLineChartDesign, MultiChartMultiLineChartDesign, MultiLineChartDesign)
from sofastats.output.charts.pie import PieChartDesign

import pandas as pd

from tests.conf import csvs_folder, sort_orders_yaml_file_path

people_csv_fpath = csvs_folder / 'people.csv'

unused_output_folder = Path.cwd()

age_groups_sorted = ['<20', '20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+']
age_groups_unsorted = ['20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+', '<20']
home_location_types_sorted = ['City', 'Town', 'Rural']

def display_val(raw: float, *, is_pct=False) -> str:
    new = str(round(raw, 3))
    if new[-2:] != '.0':
        new = new.rstrip('0')
    if is_pct:
        new += '%'
    return new

def display_amount(raw: float) -> str:
    return display_val(raw, is_pct=False)

def display_pct(raw: float) -> str:
    return display_val(raw, is_pct=True)

def _initial_category_checks(*, df_filtered: pd.DataFrame, html: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, already_checked_n_records=False):
    """
    Note - frequencies by category have % in labels so some shared logic with percentages by category
    Some things are in common between area, bar, and line.
    If by chart only - Category, Chart
    If by series only - Category, Series
    If by chart AND series - Category, Series
    """
    if series_value:  ## if by series then have to do n_record calculations out at the chart / total df level
        if not already_checked_n_records:
            raise Exception("The n_records value needs to be checked but this has to happen outside of "
                "the check_category_freqs() function call when there is a series "
                "because we don't have access to the full df")
    else:
        n_records = len(df_filtered)
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
    for n, category in enumerate(category_values_in_expected_order, 1):
        assert f'{{value: {n}, text: "{category}"}}' in html

def check_category_freqs(*, df_filtered: pd.DataFrame, html: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, chart_value: str | None = None, already_checked_n_records=False):
    _initial_category_checks(df_filtered=df_filtered, html=html,
        category_values_in_expected_order=category_values_in_expected_order,
        series_value=series_value, already_checked_n_records=already_checked_n_records)
    df_vals = df_filtered
    s_freqs = df_filtered.groupby(category_field_name).size()
    s_pcts = ((100 * df_vals.groupby(category_field_name).size()) / len(df_vals))
    category2freq = dict(s_freqs.items())
    category2pct = dict(s_pcts.items())
    category_freqs = []
    category_labels = []
    for category in category_values_in_expected_order:
        category_freq = category2freq[category]
        category_freqs.append(category_freq)
        category_pct = category2pct[category]
        if series_value is not None:
            chart_lbl = f"{category}, {series_value}<br>"
        elif chart_value is not None:
            chart_lbl = f"{category}, {chart_value}<br>"
        else:
            chart_lbl = ''
        category_label = f"'{chart_lbl}{category_freq}<br>({display_pct(category_pct)})'"
        category_labels.append(category_label)
    assert f'["vals"] = {category_freqs};' in html
    assert ("yLbls: [" + ", ".join(category_labels) + "]") in html

def check_category_pcts(*, df_filtered: pd.DataFrame, html: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str],
        series_value: str | None = None, chart_value: str | None = None, already_checked_n_records=False):
    """
    Note - frequencies by category have % in labels so some shared logic with percentages by category
    Some things are in common between area, bar, and line.
    """
    _initial_category_checks(df_filtered=df_filtered, html=html,
        category_values_in_expected_order=category_values_in_expected_order,
        series_value=series_value, already_checked_n_records=already_checked_n_records)
    df_vals = df_filtered
    s_freqs = df_filtered.groupby(category_field_name).size()
    s_pcts = ((100 * df_vals.groupby(category_field_name).size()) / len(df_vals))
    category2freq = dict(s_freqs.items())
    category2pct = dict(s_pcts.items())
    category_pcts = []  ## raw values with all decimal points so graph accurate
    category_labels = []  ## rounded values so sensible to read
    for category in category_values_in_expected_order:
        category_freq = category2freq[category]
        category_pct = category2pct[category]
        category_pcts.append(category_pct)
        if series_value is not None:
            chart_lbl = f"{category}, {series_value}<br>"
        elif chart_value is not None:
            chart_lbl = f"{category}, {chart_value}<br>"
        else:
            chart_lbl = ''
        category_label = f"'{chart_lbl}{category_freq}<br>({display_pct(category_pct)})'"
        category_labels.append(category_label)
    assert f'["vals"] = {category_pcts};' in html
    assert ("yLbls: [" + ", ".join(category_labels) + "]") in html

def check_category_averages(*, df_filtered: pd.DataFrame, html: str, field_name: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str]):
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
        category_label = f"'{display_amount(category_avg)}'"
        category_labels.append(category_label)
    assert f'["vals"] = {category_avgs};' in html
    assert ("yLbls: [" + ", ".join(category_labels) + "]") in html

def check_category_sums(*, df_filtered: pd.DataFrame, html: str, field_name: str,
        category_field_name: str, category_values_in_expected_order: Sequence[str]):
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
        category_label = f"'{display_amount(category_sum)}'"
        category_labels.append(category_label)
    assert f'["vals"] = {category_sums};' in html
    assert ("yLbls: [" + ", ".join(category_labels) + "]") in html

def test_simple_bar_chart_unsorted():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_unsorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        category_field_name=category_field_name,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_freqs(df_filtered=df, html=html,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

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
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_freqs(df_filtered=df, html=html,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

def test_simple_bar_chart_percents():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.PCT,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_pcts(df_filtered=df, html=html,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

def test_simple_bar_chart_averages():
    csv_file_path = people_csv_fpath
    field_name = 'Sleep'
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.AVG,
        field_name=field_name,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_averages(df_filtered=df, html=html, field_name=field_name,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

def test_simple_bar_chart_sums():
    csv_file_path = people_csv_fpath
    field_name = 'Sleep'
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = SimpleBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.SUM,
        field_name=field_name,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_sums(df_filtered=df, html=html, field_name=field_name,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

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
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html
        df_filtered = df.loc[df[chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html,
            category_field_name=category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

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
    print(html)
    df = pd.read_csv(csv_file_path)
    n_records = len(df)  ## when no chart, but series, have to do it here
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    series_values = df[series_field_name].unique()
    for series_value in series_values:  ## not testing whether in the right order
        assert f'["label"] = "{series_value}"' in html  ## series
        df_filtered = df.loc[df[series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html,
            category_field_name=category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

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
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html  ## chart
        series_values = df[series_field_name].unique()
        df_chart = df[df[chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
        for series_value in series_values:  ## not testing whether in the right order
            assert f'["label"] = "{series_value}"' in html  ## series
            df_filtered = df.loc[(df[chart_field_name] == chart_value) & (df[series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html,
                category_field_name=category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_multi_chart_clustered_percents_bar_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    series_field_name = 'Country'
    chart_field_name = 'Tertiary Qualifications'
    design = MultiChartClusteredBarChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.PCT,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        series_field_name=series_field_name,
        series_sort_order=SortOrder.CUSTOM,
        chart_field_name=chart_field_name,
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html  ## chart
        series_values = df[series_field_name].unique()
        df_chart = df[df[chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
        for series_value in series_values:  ## not testing whether in the right order
            assert f'["label"] = "{series_value}"' in html  ## series
            df_filtered = df.loc[(df[chart_field_name] == chart_value) & (df[series_field_name] == series_value)]
            check_category_pcts(df_filtered=df_filtered, html=html,
                category_field_name=category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_line_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = LineChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_freqs(df_filtered=df, html=html,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

def test_multi_line_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    series_field_name = 'Country'
    design = MultiLineChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        series_field_name=series_field_name,
        series_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    series_values = df[series_field_name].unique()
    for series_value in series_values:  ## not testing whether in the right order
        assert f'["label"] = "{series_value}"' in html  ## series
        df_filtered = df.loc[df[series_field_name] == series_value]
        check_category_freqs(df_filtered=df_filtered, html=html,
            category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order,
            series_value=series_value, already_checked_n_records=True)

def test_multi_chart_line_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    chart_field_name = 'Country'
    design = MultiChartLineChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name=chart_field_name,
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html  ## chart
        df_filtered = df.loc[df[chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html,
            category_field_name=category_field_name,
            category_values_in_expected_order=category_values_in_expected_order,
            chart_value=chart_value, already_checked_n_records=True)

def test_multi_chart_multi_line_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Home Location Type'
    category_values_in_expected_order = home_location_types_sorted
    series_field_name = 'Country'
    chart_field_name = 'Age Group'
    design = MultiChartMultiLineChartDesign(
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
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html  ## chart
        series_values = df[series_field_name].unique()
        df_chart = df[df[chart_field_name] == chart_value]
        n_records = len(df_chart)  ## filter to chart
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
        for series_value in series_values:  ## not testing whether in the right order
            assert f'["label"] = "{series_value}"' in html  ## series
            df_filtered = df.loc[(df[chart_field_name] == chart_value) & (df[series_field_name] == series_value)]
            check_category_freqs(df_filtered=df_filtered, html=html,
                category_field_name=category_field_name,
                category_values_in_expected_order=category_values_in_expected_order,
                series_value=series_value, already_checked_n_records=True)

def test_area_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    design = AreaChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    check_category_freqs(df_filtered=df, html=html,
        category_field_name=category_field_name, category_values_in_expected_order=category_values_in_expected_order)

def test_multi_chart_area_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Age Group'
    category_values_in_expected_order = age_groups_sorted
    chart_field_name = 'Country'
    design = MultiChartAreaChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name=chart_field_name,
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    chart_values = df[chart_field_name].unique()
    for chart_value in chart_values:  ## not testing whether in the right order
        assert f"{chart_field_name}: {chart_value}" in html
        df_filtered = df.loc[df[chart_field_name] == chart_value]
        check_category_freqs(df_filtered=df_filtered, html=html,
            category_field_name=category_field_name,
            category_values_in_expected_order=category_values_in_expected_order, chart_value=chart_value)

def test_pie_chart():
    csv_file_path = people_csv_fpath
    category_field_name = 'Country'
    design = PieChartDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name=category_field_name,
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(csv_file_path)
    ## TODO: pass n_records through to Pie Charts!
    """
    {"val": 2227, "label": "USA", "tool_tip": "2227<br>(44.54%)"},
    {"val": 897, "label": "NZ", "tool_tip": "897<br>(17.94%)"},
    {"val": 1140, "label": "South Korea", "tool_tip": "1140<br>(22.8%)"},
    {"val": 736, "label": "Denmark", "tool_tip": "736<br>(14.72%)"}
    """

if __name__ == "__main__":
    pass
    # test_simple_bar_chart_unsorted()
    # test_simple_bar_chart_sorted()
    # test_simple_bar_chart_percents()
    # test_simple_bar_chart_averages()
    # test_simple_bar_chart_sums()
    # test_multi_chart_bar_chart()
    # test_clustered_bar_chart()
    # test_multi_chart_clustered_bar_chart()
    # test_multi_chart_clustered_percents_bar_chart()
    # test_line_chart()
    # test_multi_line_chart()
    # test_multi_chart_line_chart()
    # test_multi_chart_multi_line_chart()
    # test_area_chart()
    # test_multi_chart_area_chart()
    test_pie_chart()
