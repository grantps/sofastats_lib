## To run the demo examples, install the sofastats_examples package
## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py

from sofastats.conf.main import SortOrder
from sofastats.output.stats.anova import AnovaDesign
from sofastats.output.stats.chi_square import ChiSquareDesign
from sofastats.output.stats.kruskal_wallis_h import KruskalWallisHDesign
from sofastats.output.stats.mann_whitney_u import MannWhitneyUDesign
from sofastats.output.stats.normality import NormalityDesign
from sofastats.output.stats.pearsons_r import PearsonsRDesign
from sofastats.output.stats.spearmans_r import SpearmansRDesign
from sofastats.output.stats.independent_t_test import IndependentTTestDesign
from sofastats.output.stats.paired_t_test import PairedTTestDesign
from sofastats.output.stats.wilcoxon_signed_ranks import WilcoxonSignedRanksDesign

from sofastats_examples.scripts.conf import (output_folder, people_csv_file_path, sort_orders_yaml_file_path)

def anova_black_pastel_style(csv_file_path):
    design = AnovaDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_anova_age_by_country_black_pastel_style.html',
        output_title='ANOVA - Black Pastel Style',
        show_in_web_browser=True,
        style_name='black_pastel',
        grouping_field_name='Country',
        grouping_field_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    return design

def anova_red_spirals_style(csv_file_path):
    design = AnovaDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_anova_age_by_country_red_spirals_style.html',
        output_title='ANOVA - Red Spirals Design',
        show_in_web_browser=True,
        style_name='red_spirals',
        grouping_field_name='Country',
        grouping_field_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    return design

def chi_square(csv_file_path):
    design = ChiSquareDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_chi_square_stats.html',
        output_title='Chi Square Test',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        variable_a_name='Age Group',
        variable_a_sort_order=SortOrder.CUSTOM,
        variable_b_name='Country',
        variable_b_sort_order=SortOrder.CUSTOM,
        decimal_points=3,
        show_workings=True,
    )
    return design

def kruskal_wallis_h(csv_file_path):
    design = KruskalWallisHDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_kruskal_wallis_h.html',
        output_title='Kruskal-Wallis H Test',
        show_in_web_browser=True,
        style_name='default',
        grouping_field_name='Country',
        grouping_field_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        decimal_points=3,
        show_workings=True,
    )
    return design

def mann_whitney_u(csv_file_path):
    design = MannWhitneyUDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_mann_whitney_u_age_by_country.html',
        output_title='Mann-Whitney U',
        show_in_web_browser=True,
        style_name='default',
        grouping_field_name='Country',
        group_a_value='South Korea',
        group_b_value='NZ',
        measure_field_name='Weight Time 1',
        decimal_points=3,
        show_workings=True,
    )
    return design

def normality(csv_file_path):
    design = NormalityDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_normality_age_vs_weight.html',
        output_title='Normality Test',
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 2',
    )
    return design

def pearsons_r(csv_file_path):
    design = PearsonsRDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pearsons_r.html',
        output_title="Pearson's R Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 1',
        decimal_points=3,
    )
    return design

def spearmans_r(csv_file_path):
    design = SpearmansRDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_spearmans_r.html',
        output_title="Spearman's R Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 1',
        show_workings=True,
    )
    return design

def independent_t_test(csv_file_path):
    design = IndependentTTestDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_ttest_indep_age_by_country_from_item.html',
        output_title="Independent T-Test",
        show_in_web_browser=True,
        style_name='default',
        grouping_field_name='Country',
        group_a_value='South Korea',
        group_b_value='USA',
        measure_field_name='Age',
    )
    return design

def paired_t_test(csv_file_path):
    design = PairedTTestDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_t_test_paired.html',
        output_title="Paired T-Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Weight Time 1',
        variable_b_name='Weight Time 2',
    )
    return design

def wilcoxon_signed_ranks(csv_file_path):
    design = WilcoxonSignedRanksDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_wilcoxon_signed_ranks.html',
        output_title="Wilcoxon Signed Ranks",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Weight Time 1',
        variable_b_name='Weight Time 2',
        show_workings=True,
    )
    return design

