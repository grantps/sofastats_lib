from pathlib import Path

from sofastats.conf.main import ChartMetric, SortOrder
from sofastats.output.charts.bar import (
    ClusteredBarChartDesign, MultiChartBarChartDesign, MultiChartClusteredBarChartDesign, SimpleBarChartDesign)
from sofastats.output.charts.line import LineChartDesign, MultiLineChartDesign

import pandas as pd

from tests.conf import csvs_folder, sort_orders_yaml_file_path

people_csv_fpath = csvs_folder / 'people.csv'

unused_output_folder = Path.cwd()

country_categories_sorted = ['<20', '20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+']
country_categories_unsorted = ['20 to <30', '30 to <40', '40 to <50', '50 to <60', '60 to <70', '70 to <80', '80+', '<20']

def display_vals(raw: float, *, is_pct=False) -> str:
    new = str(round(raw, 3))
    if new[-2:] != '.0':
        new = new.rstrip('0')
    if is_pct:
        new += '%'
    return new

def display_amounts(raw: float) -> str:
    return display_vals(raw, is_pct=False)

def display_pcts(raw: float) -> str:
    return display_vals(raw, is_pct=True)

def test_simple_bar_chart_unsorted():
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        category_field_name='Age Group',
    )
    html = design.to_html_design().html_item_str
    # print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_unsorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    ## category vals
    val_under_20 = len(df.loc[df['Age Group'] == '<20'])
    val_20_30 = len(df.loc[df['Age Group'] == '20 to <30'])
    val_30_40 = len(df.loc[df['Age Group'] == '30 to <40'])
    val_40_50 = len(df.loc[df['Age Group'] == '40 to <50'])
    val_50_60 = len(df.loc[df['Age Group'] == '50 to <60'])
    val_60_70 = len(df.loc[df['Age Group'] == '60 to <70'])
    val_70_80 = len(df.loc[df['Age Group'] == '70 to <80'])
    val_80_plus = len(df.loc[df['Age Group'] == '80+'])
    html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
    assert f'["vals"] = [{val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}, {val_under_20}];' in html2use
    ## category labels
    df_vals = ((100 * df.groupby('Age Group').size()) / len(df))
    val_under_20_2 = display_pcts(df_vals.loc[['<20']].values[0])
    val_20_30_2 = display_pcts(df_vals.loc[['20 to <30']].values[0])
    val_30_40_2 = display_pcts(df_vals.loc[['30 to <40']].values[0])
    val_40_50_2 = display_pcts(df_vals.loc[['40 to <50']].values[0])
    val_50_60_2 = display_pcts(df_vals.loc[['50 to <60']].values[0])
    val_60_70_2 = display_pcts(df_vals.loc[['60 to <70']].values[0])
    val_70_80_2 = display_pcts(df_vals.loc[['70 to <80']].values[0])
    val_80_plus_2 = display_pcts(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
    assert (f"yLbls: ["
        f"'{val_20_30}<br>({val_20_30_2})', "
        f"'{val_30_40}<br>({val_30_40_2})', "
        f"'{val_40_50}<br>({val_40_50_2})', "
        f"'{val_50_60}<br>({val_50_60_2})', "
        f"'{val_60_70}<br>({val_60_70_2})', "
        f"'{val_70_80}<br>({val_70_80_2})', "
        f"'{val_80_plus}<br>({val_80_plus_2})', "
        f"'{val_under_20}<br>({val_under_20_2})']") in html2use

def check_category_age_group(html: str):
    """
    Some things are in common between area, bar, and line.
    """
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_sorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    df_vals = df
    val_under_20 = len(df_vals.loc[df_vals['Age Group'] == '<20'])
    val_20_30 = len(df_vals.loc[df_vals['Age Group'] == '20 to <30'])
    val_30_40 = len(df_vals.loc[df_vals['Age Group'] == '30 to <40'])
    val_40_50 = len(df_vals.loc[df_vals['Age Group'] == '40 to <50'])
    val_50_60 = len(df_vals.loc[df_vals['Age Group'] == '50 to <60'])
    val_60_70 = len(df_vals.loc[df_vals['Age Group'] == '60 to <70'])
    val_70_80 = len(df_vals.loc[df_vals['Age Group'] == '70 to <80'])
    val_80_plus = len(df_vals.loc[df_vals['Age Group'] == '80+'])
    html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
    assert f'["vals"] = [{val_under_20}, {val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}];' in html2use
    df_vals = ((100 * df.groupby('Age Group').size()) / len(df))
    val_under_20_2 = display_pcts(df_vals.loc[['<20']].values[0])
    val_20_30_2 = display_pcts(df_vals.loc[['20 to <30']].values[0])
    val_30_40_2 = display_pcts(df_vals.loc[['30 to <40']].values[0])
    val_40_50_2 = display_pcts(df_vals.loc[['40 to <50']].values[0])
    val_50_60_2 = display_pcts(df_vals.loc[['50 to <60']].values[0])
    val_60_70_2 = display_pcts(df_vals.loc[['60 to <70']].values[0])
    val_70_80_2 = display_pcts(df_vals.loc[['70 to <80']].values[0])
    val_80_plus_2 = display_pcts(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
    assert (f"yLbls: ["
        f"'{val_under_20}<br>({val_under_20_2})', "
        f"'{val_20_30}<br>({val_20_30_2})', "
        f"'{val_30_40}<br>({val_30_40_2})', "
        f"'{val_40_50}<br>({val_40_50_2})', "
        f"'{val_50_60}<br>({val_50_60_2})', "
        f"'{val_60_70}<br>({val_60_70_2})', "
        f"'{val_70_80}<br>({val_70_80_2})', "
        f"'{val_80_plus}<br>({val_80_plus_2})']") in html2use

def test_simple_bar_chart_sorted():
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    check_category_age_group(html)

def test_simple_bar_chart_percents():
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        output_title="Simple Bar Chart (Percents)",
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.PCT,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_sorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    df_vals = ((100 * df.groupby('Age Group').size()) / len(df))
    val_under_20 = float(df_vals.loc[['<20']].values[0])
    val_20_30 = float(df_vals.loc[['20 to <30']].values[0])
    val_30_40 = float(df_vals.loc[['30 to <40']].values[0])
    val_40_50 = float(df_vals.loc[['40 to <50']].values[0])
    val_50_60 = float(df_vals.loc[['50 to <60']].values[0])
    val_60_70 = float(df_vals.loc[['60 to <70']].values[0])
    val_70_80 = float(df_vals.loc[['70 to <80']].values[0])
    val_80_plus = float(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
    assert f'["vals"] = [{val_under_20}, {val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}];' in html2use
    ## freq for label
    df_vals = df
    val_under_20 = len(df_vals.loc[df_vals['Age Group'] == '<20'])
    val_20_30 = len(df_vals.loc[df_vals['Age Group'] == '20 to <30'])
    val_30_40 = len(df_vals.loc[df_vals['Age Group'] == '30 to <40'])
    val_40_50 = len(df_vals.loc[df_vals['Age Group'] == '40 to <50'])
    val_50_60 = len(df_vals.loc[df_vals['Age Group'] == '50 to <60'])
    val_60_70 = len(df_vals.loc[df_vals['Age Group'] == '60 to <70'])
    val_70_80 = len(df_vals.loc[df_vals['Age Group'] == '70 to <80'])
    val_80_plus = len(df_vals.loc[df_vals['Age Group'] == '80+'])
    ## % for label
    df_vals = ((100 * df.groupby('Age Group').size()) / len(df))
    val_under_20_2 = display_pcts(df_vals.loc[['<20']].values[0])
    val_20_30_2 = display_pcts(df_vals.loc[['20 to <30']].values[0])
    val_30_40_2 = display_pcts(df_vals.loc[['30 to <40']].values[0])
    val_40_50_2 = display_pcts(df_vals.loc[['40 to <50']].values[0])
    val_50_60_2 = display_pcts(df_vals.loc[['50 to <60']].values[0])
    val_60_70_2 = display_pcts(df_vals.loc[['60 to <70']].values[0])
    val_70_80_2 = display_pcts(df_vals.loc[['70 to <80']].values[0])
    val_80_plus_2 = display_pcts(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
    assert (f"yLbls: ["
        f"'{val_under_20}<br>({val_under_20_2})', "
        f"'{val_20_30}<br>({val_20_30_2})', "
        f"'{val_30_40}<br>({val_30_40_2})', "
        f"'{val_40_50}<br>({val_40_50_2})', "
        f"'{val_50_60}<br>({val_50_60_2})', "
        f"'{val_60_70}<br>({val_60_70_2})', "
        f"'{val_70_80}<br>({val_70_80_2})', "
        f"'{val_80_plus}<br>({val_80_plus_2})']") in html2use

def test_simple_bar_chart_averages():
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.AVG,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_sorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    df_vals = df.groupby('Age Group')['Sleep'].mean()
    val_under_20 = float(df_vals.loc[['<20']].values[0])
    val_20_30 = float(df_vals.loc[['20 to <30']].values[0])
    val_30_40 = float(df_vals.loc[['30 to <40']].values[0])
    val_40_50 = float(df_vals.loc[['40 to <50']].values[0])
    val_50_60 = float(df_vals.loc[['50 to <60']].values[0])
    val_60_70 = float(df_vals.loc[['60 to <70']].values[0])
    val_70_80 = float(df_vals.loc[['70 to <80']].values[0])
    val_80_plus = float(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
    assert f'["vals"] = [{val_under_20}, {val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}];' in html2use
    val_under_20 = display_amounts(round(float(df_vals.loc[['<20']].values[0]), 3))
    val_20_30 = display_amounts(round(float(df_vals.loc[['20 to <30']].values[0]), 3))
    val_30_40 = display_amounts(round(float(df_vals.loc[['30 to <40']].values[0]), 3))
    val_40_50 = display_amounts(round(float(df_vals.loc[['40 to <50']].values[0]), 3))
    val_50_60 = display_amounts(round(float(df_vals.loc[['50 to <60']].values[0]), 3))
    val_60_70 = display_amounts(round(float(df_vals.loc[['60 to <70']].values[0]), 3))
    val_70_80 = display_amounts(round(float(df_vals.loc[['70 to <80']].values[0]), 3))
    val_80_plus = display_amounts(round(float(df_vals.loc[['80+']].values[0]), 3))
    html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
    assert f"yLbls: ['{val_under_20}', '{val_20_30}', '{val_30_40}', '{val_40_50}', '{val_50_60}', '{val_60_70}', '{val_70_80}', '{val_80_plus}']" in html2use

def test_simple_bar_chart_sums():
    design = SimpleBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        metric=ChartMetric.SUM,
        field_name='Sleep',
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_sorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    df_vals = df.groupby('Age Group')['Sleep'].sum()
    val_under_20 = float(df_vals.loc[['<20']].values[0])
    val_20_30 = float(df_vals.loc[['20 to <30']].values[0])
    val_30_40 = float(df_vals.loc[['30 to <40']].values[0])
    val_40_50 = float(df_vals.loc[['40 to <50']].values[0])
    val_50_60 = float(df_vals.loc[['50 to <60']].values[0])
    val_60_70 = float(df_vals.loc[['60 to <70']].values[0])
    val_70_80 = float(df_vals.loc[['70 to <80']].values[0])
    val_80_plus = float(df_vals.loc[['80+']].values[0])
    html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
    assert f'["vals"] = [{val_under_20}, {val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}];' in html2use
    val_under_20 = display_amounts(round(float(df_vals.loc[['<20']].values[0]), 3))
    val_20_30 = display_amounts(round(float(df_vals.loc[['20 to <30']].values[0]), 3))
    val_30_40 = display_amounts(round(float(df_vals.loc[['30 to <40']].values[0]), 3))
    val_40_50 = display_amounts(round(float(df_vals.loc[['40 to <50']].values[0]), 3))
    val_50_60 = display_amounts(round(float(df_vals.loc[['50 to <60']].values[0]), 3))
    val_60_70 = display_amounts(round(float(df_vals.loc[['60 to <70']].values[0]), 3))
    val_70_80 = display_amounts(round(float(df_vals.loc[['70 to <80']].values[0]), 3))
    val_80_plus = display_amounts(round(float(df_vals.loc[['80+']].values[0]), 3))
    html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
    assert f"yLbls: ['{val_under_20}', '{val_20_30}', '{val_30_40}', '{val_40_50}', '{val_50_60}', '{val_60_70}', '{val_70_80}', '{val_80_plus}']" in html2use

def test_multi_bar_chart():
    design = MultiChartBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        chart_field_name='Country',
        chart_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_chart_records = df.groupby('Country').size()
    for n_records in n_chart_records:
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    assert '{value: 1, text: "City"}' in html
    assert '{value: 2, text: "Town"}' in html
    assert '{value: 3, text: "Rural"}' in html
    countries = df['Country'].unique()
    for country in countries:  ## not testing whether in the right order
        assert f"Country: {country}" in html
        home_locations = df[df['Country'] == country].groupby('Home Location Type').size()
        home_location_freqs = dict(home_locations.items())
        vals = []
        for category in ['City', 'Town', 'Rural']:
            vals.append(home_location_freqs[category])
        vals_declaration = f'["vals"] = {vals};'
        # print(vals_declaration)
        assert vals_declaration in html
        sub_total = sum(vals)
        for home_location, val in home_location_freqs.items():
            assert f"{home_location}, {country}<br>{val}<br>({round((100 * val) / sub_total, 3)}%)" in html

def test_clustered_bar_chart():
    design = ClusteredBarChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Home Location Type',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    assert '{value: 1, text: "City"}' in html
    assert '{value: 2, text: "Town"}' in html
    assert '{value: 3, text: "Rural"}' in html
    countries = df['Country'].unique()
    for country in countries:  ## not testing whether in the right order
        assert f'["label"] = "{country}"' in html  ## series
        home_locations = df[df['Country'] == country].groupby('Home Location Type').size()
        home_location_freqs = dict(home_locations.items())
        vals = []
        for category in ['City', 'Town', 'Rural']:
            vals.append(home_location_freqs[category])
        vals_declaration = f'["vals"] = {vals};'
        # print(vals_declaration)
        assert vals_declaration in html  ## category vals
        sub_total = sum(vals)
        for home_location, val in home_location_freqs.items():
            assert f"{home_location}, {country}<br>{val}<br>({round((100 * val) / sub_total, 3)}%)" in html  ## category labels

def test_multi_chart_clustered_bar_chart():
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
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_chart_records = df.groupby('Tertiary Qualifications').size()
    for n_records in n_chart_records:
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    assert '{value: 1, text: "City"}' in html
    assert '{value: 2, text: "Town"}' in html
    assert '{value: 3, text: "Rural"}' in html
    quals = df['Tertiary Qualifications'].unique()
    for qual in quals:  ## not testing whether in the right order
        assert f"Tertiary Qualifications: {qual}" in html  ## chart
        countries = df['Country'].unique()
        for country in countries:  ## not testing whether in the right order
            assert f'["label"] = "{country}"' in html  ## series
            s_home_locations = df.loc[(df['Tertiary Qualifications'] == qual) & (df['Country'] == country)].groupby('Home Location Type').size()
            home_location_freqs = dict(s_home_locations.items())
            vals = []
            for category in ['City', 'Town', 'Rural']:
                vals.append(home_location_freqs[category])
            vals_declaration = f'["vals"] = {vals};'
            # print(vals_declaration)
            assert vals_declaration in html  ## category val
            sub_total = sum(vals)
            for home_location, val in home_location_freqs.items():
                assert f"{home_location}, {country}<br>{val}<br>({round((100 * val) / sub_total, 3)}%)" in html  ## category label

def test_multi_chart_clustered_percents_bar_chart():
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
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_chart_records = df.groupby('Tertiary Qualifications').size()
    for n_records in n_chart_records:
        assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    assert '{value: 1, text: "City"}' in html
    assert '{value: 2, text: "Town"}' in html
    assert '{value: 3, text: "Rural"}' in html
    quals = df['Tertiary Qualifications'].unique()
    for qual in quals:  ## not testing whether in the right order
        assert f"Tertiary Qualifications: {qual}" in html  ## chart
        countries = df['Country'].unique()
        for country in countries:  ## not testing whether in the right order
            assert f'["label"] = "{country}"' in html  ## series
            df2use = df.loc[(df['Tertiary Qualifications'] == qual) & (df['Country'] == country)]
            s_home_locations_pcts = ((100 * df2use.groupby('Home Location Type').size()) / len(df2use))
            home_location_pcts = dict(s_home_locations_pcts.items())
            s_home_locations_freqs = df2use.groupby('Home Location Type').size()
            home_location_freqs = dict(s_home_locations_freqs.items())
            pct_vals = []
            for category in ['City', 'Town', 'Rural']:
                pct_vals.append(home_location_pcts[category])
            pct_vals_declaration = f'["vals"] = {pct_vals};'
            # print(pct_vals_declaration)
            assert pct_vals_declaration in html  ## category val
            sub_total = len(df2use)
            for home_location, freq in home_location_freqs.items():
                assert f"{home_location}, {country}<br>{freq}<br>({round((100 * freq) / sub_total, 3)}%)" in html  ## category label

def test_line_chart():
    design = LineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    check_category_age_group(html)

def test_multi_line_chart():
    design = MultiLineChartDesign(
        csv_file_path=people_csv_fpath,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        category_field_name='Age Group',
        category_sort_order=SortOrder.CUSTOM,
        series_field_name='Country',
        series_sort_order=SortOrder.CUSTOM,
    )
    html = design.to_html_design().html_item_str
    print(html)
    df = pd.read_csv(people_csv_fpath)
    n_records = len(df)
    assert f'conf["n_records"] = "N = {n_records:,}";' in html
    ## expected categories
    for n, country_category in enumerate(country_categories_sorted, 1):
        assert f'{{value: {n}, text: "{country_category}"}}' in html
    countries = df['Country'].unique()
    for country in countries:  ## not testing whether in the right order
        assert f'["label"] = "{country}"' in html  ## series

        ## TODO: use dicts instead? Everywhere?

        ## category vals
        df2use = df.loc[df['Country'] == country]
        df_vals = df2use
        val_under_20 = len(df_vals.loc[df_vals['Age Group'] == '<20'])
        val_20_30 = len(df_vals.loc[df_vals['Age Group'] == '20 to <30'])
        val_30_40 = len(df_vals.loc[df_vals['Age Group'] == '30 to <40'])
        val_40_50 = len(df_vals.loc[df_vals['Age Group'] == '40 to <50'])
        val_50_60 = len(df_vals.loc[df_vals['Age Group'] == '50 to <60'])
        val_60_70 = len(df_vals.loc[df_vals['Age Group'] == '60 to <70'])
        val_70_80 = len(df_vals.loc[df_vals['Age Group'] == '70 to <80'])
        val_80_plus = len(df_vals.loc[df_vals['Age Group'] == '80+'])
        html2use = html[html.index('series_00["vals"]'):]  ## so test output shows useful output before truncated
        assert f'["vals"] = [{val_under_20}, {val_20_30}, {val_30_40}, {val_40_50}, {val_50_60}, {val_60_70}, {val_70_80}, {val_80_plus}];' in html2use
        ## category labels
        df_vals = ((100 * df2use.groupby('Age Group').size()) / len(df2use))
        val_under_20_2 = display_pcts(df_vals.loc[['<20']].values[0])
        val_20_30_2 = display_pcts(df_vals.loc[['20 to <30']].values[0])
        val_30_40_2 = display_pcts(df_vals.loc[['30 to <40']].values[0])
        val_40_50_2 = display_pcts(df_vals.loc[['40 to <50']].values[0])
        val_50_60_2 = display_pcts(df_vals.loc[['50 to <60']].values[0])
        val_60_70_2 = display_pcts(df_vals.loc[['60 to <70']].values[0])
        val_70_80_2 = display_pcts(df_vals.loc[['70 to <80']].values[0])
        val_80_plus_2 = display_pcts(df_vals.loc[['80+']].values[0])
        html2use = html[html.index('yLbls: ['):]  ## so test output shows useful output before truncated
        assert (f"yLbls: ["
            f"'<20, {country}<br>{val_under_20}<br>({val_under_20_2})', "
            f"'20 to <30, {country}<br>{val_20_30}<br>({val_20_30_2})', "
            f"'30 to <40, {country}<br>{val_30_40}<br>({val_30_40_2})', "
            f"'40 to <50, {country}<br>{val_40_50}<br>({val_40_50_2})', "
            f"'50 to <60, {country}<br>{val_50_60}<br>({val_50_60_2})', "
            f"'60 to <70, {country}<br>{val_60_70}<br>({val_60_70_2})', "
            f"'70 to <80, {country}<br>{val_70_80}<br>({val_70_80_2})', "
            f"'80+, {country}<br>{val_80_plus}<br>({val_80_plus_2})']") in html2use

if __name__ == "__main__":
    pass
    # test_simple_bar_chart_unsorted()
    # test_simple_bar_chart_sorted()
    # test_simple_bar_chart_percents()
    # test_simple_bar_chart_averages()
    # test_simple_bar_chart_sums()
    # test_multi_bar_chart()
    # test_clustered_bar_chart()
    # test_multi_chart_clustered_bar_chart()
    # test_multi_chart_clustered_percents_bar_chart()
    # test_line_chart()
    # test_multi_line_chart()
