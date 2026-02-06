"""
Strategy - for each statistical test, compare the result against two trusted sources:
1) the original stats.py
2) the widely used and scrutinised SOFA Statistics code
"""
from functools import partial
import tempfile

from sofastats.conf.main import SortOrder
from sofastats.output.stats.anova import AnovaDesign
from sofastats.output.stats.chi_square import ChiSquareDesign
from tests.conf import age_groups_sorted, countries_sorted, people_csv_fpath, sort_orders_yaml_file_path
from tests.reference_stats_library import anova as stats_anova, chisquare_df_corrected as stats_chi_square
from tests.utils import sort_index_following_pattern
# from tests.sofastatistics_core_stats import anova as ss_anova

import pandas as pd

round_to_11dp = partial(round, ndigits=11)

def test_anova():
    csv_file_path = people_csv_fpath
    grouping_field_name = 'Country'
    group_values = ['South Korea', 'NZ', 'USA']
    measure_field_name = 'Age'
    design = AnovaDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        grouping_field_name=grouping_field_name,
        grouping_field_sort_order=SortOrder.VALUE,
        group_values=group_values,
        measure_field_name=measure_field_name,
        high_precision_required=False,
    )
    # design.make_output()
    result = design.to_result()
    print(result)
    df_raw = pd.read_csv(people_csv_fpath)
    df = df_raw.loc[df_raw[grouping_field_name].isin(group_values), [grouping_field_name, measure_field_name]]
    data_south_korea = df.loc[df[grouping_field_name] == 'South Korea', measure_field_name].tolist()
    data_nz = df.loc[df[grouping_field_name] == 'NZ', measure_field_name].tolist()
    data_usa = df.loc[df[grouping_field_name] == 'USA', measure_field_name].tolist()
    stats_f, stats_prob = stats_anova(data_south_korea, data_nz, data_usa)
    assert round_to_11dp(result.F) == round_to_11dp(stats_f)  ## 1.25871675527 88687 ~= 1.25871675527 92649
    assert round_to_11dp(result.p) == round_to_11dp(stats_prob)  ## 0.284123842228 97413 ~= 0.284123842228 84

def test_chi_square():
    orig_csv_file_path = people_csv_fpath
    df_unfiltered = pd.read_csv(orig_csv_file_path)
    df = df_unfiltered.loc[
        (df_unfiltered['Age Group'].isin(['<20', '20 to <30'])) & (df_unfiltered['Country'].isin(['Denmark', 'NZ']))]
    temp = tempfile.NamedTemporaryFile()
    df.to_csv(temp.name, index=False)
    csv_file_path = temp.name
    variable_a_name = 'Age Group'
    variable_b_name = 'Country'
    design = ChiSquareDesign(
        csv_file_path=csv_file_path,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        variable_a_name=variable_a_name, variable_a_sort_order=SortOrder.CUSTOM,
        variable_b_name=variable_b_name, variable_b_sort_order=SortOrder.CUSTOM,
    )
    design.make_output()
    result = design.to_result()
    print(result)

    under_20_nz_freq = len(df.loc[(df['Age Group'] == '<20') & (df['Country'] == 'NZ')])
    under_20_denmark_freq = len(df.loc[(df['Age Group'] == '<20') & (df['Country'] == 'Denmark')])
    twenty_to_under_30_nz_freq = len(df.loc[(df['Age Group'] == '20 to <30') & (df['Country'] == 'NZ')])
    twenty_to_under_30_denmark_freq = len(df.loc[(df['Age Group'] == '20 to <30') & (df['Country'] == 'Denmark')])

    total_freq = len(df)

    nz_freq = len(df.loc[df['Country'] == 'NZ'])
    denmark_freq = len(df.loc[df['Country'] == 'Denmark'])
    nz_fraction = nz_freq / total_freq
    denmark_fraction = denmark_freq / total_freq

    under_20_freq = len(df.loc[df['Age Group'] == '<20'])
    twenty_to_under_30_freq = len(df.loc[df['Age Group'] == '20 to <30'])
    under_20_fraction = under_20_freq / total_freq
    twenty_to_under_30_fraction = twenty_to_under_30_freq / total_freq

    expected_under_20_nz_freq = total_freq * under_20_fraction * nz_fraction
    expected_under_20_denmark_freq = total_freq * under_20_fraction * denmark_fraction
    expected_twenty_to_under_30_nz_freq = total_freq * twenty_to_under_30_fraction * nz_fraction
    expected_twenty_to_under_30_denmark_freq = total_freq * twenty_to_under_30_fraction * denmark_fraction

    observed_freqs_by_country_within_age_group = [
        under_20_nz_freq, under_20_denmark_freq,
        twenty_to_under_30_nz_freq, twenty_to_under_30_denmark_freq]
    expected_freqs_by_country_within_age_group = [
        expected_under_20_nz_freq, expected_under_20_denmark_freq,
        expected_twenty_to_under_30_nz_freq, expected_twenty_to_under_30_denmark_freq]

    n_variable_a_vals = len(df['Age Group'].unique())
    n_variable_b_vals = len(df['Country'].unique())
    degrees_of_freedom = (n_variable_a_vals - 1) * (n_variable_b_vals - 1)
    stats_chisq, stats_p = stats_chi_square(
        f_obs=observed_freqs_by_country_within_age_group, f_exp=expected_freqs_by_country_within_age_group,
        df=degrees_of_freedom)

    assert round_to_11dp(result.p) == round_to_11dp(stats_p)
    assert round_to_11dp(result.chi_square) == round_to_11dp(stats_chisq)

if __name__ == '__main__':
    pass
    # test_anova()
    # test_chi_square()
