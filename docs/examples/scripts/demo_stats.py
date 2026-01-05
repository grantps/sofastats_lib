from pathlib import Path
import sqlite3 as sqlite

from sofastats.output.stats.anova import AnovaDesign
from sofastats.output.stats.chi_square import ChiSquareDesign
from sofastats.output.stats.kruskal_wallis_h import KruskalWallisHDesign
from sofastats.output.stats.mann_whitney_u import MannWhitneyUDesign
from sofastats.output.stats.normality import NormalityDesign
from sofastats.output.stats.pearsons_r import PearsonsRDesign
from sofastats.output.stats.spearmans_r import SpearmansRDesign
from sofastats.output.stats.ttest_indep import TTestIndepDesign
from sofastats.output.stats.ttest_paired import TTestPairedDesign
from sofastats.output.stats.wilcoxon_signed_ranks import WilcoxonSignedRanksDesign

from conf import (education_csv_file_path, output_folder, people_csv_file_path,
    sort_orders_yaml_file_path, sports_csv_file_path, sqlite_demo_db_file_path)

def run_anova(csv_file_path):
    stats_design = AnovaDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_anova_age_by_country.html',
        output_title='ANOVA',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='prestige_screen',
        grouping_field_name='Country',
        group_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        high_precision_required=False,
        decimal_points=3,
    )
    stats_design.make_output()

def run_chi_square(csv_file_path):
    stats_design = ChiSquareDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_chi_square_stats.html',
        output_title='Chi Square Test',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        variable_a_name='Age Group',
        variable_b_name='Country',
        decimal_points=3,
        show_workings=True,
    )
    stats_design.make_output()

def run_kruskal_wallis_h(csv_file_path):
    stats_design = KruskalWallisHDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_kruskal_wallis_h.html',
        output_title='Kruskal-Wallis H Test',
        show_in_web_browser=True,
        sort_orders_yaml_file_path=sort_orders_yaml_file_path,
        style_name='default',
        grouping_field_name='Country',
        group_values=['South Korea', 'NZ', 'USA'],
        measure_field_name='Age',
        decimal_points=3,
        show_workings=True,
    )
    stats_design.make_output()

def run_mann_whitney_u(csv_file_path):
    stats_design = MannWhitneyUDesign(
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
    stats_design.make_output()

def run_normality(csv_file_path):
    stats_design = NormalityDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_normality_age_vs_weight.html',
        output_title='Normality Test',
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 2',
    )
    stats_design.make_output()

def run_pearsons_r(csv_file_path):
    stats_design = PearsonsRDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_pearsons_r.html',
        output_title="Pearson's R Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 1',
        decimal_points=3,
    )
    stats_design.make_output()

def run_spearmans_r(csv_file_path):
    stats_design = SpearmansRDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_spearmans_r.html',
        output_title="Spearman's R Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Age',
        variable_b_name='Weight Time 1',
        show_workings=True,
    )
    stats_design.make_output()

def run_ttest_indep(csv_file_path):
    stats_design = TTestIndepDesign(
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
    stats_design.make_output()

def run_t_test_paired(csv_file_path):
    stats_design = TTestPairedDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_t_test_paired.html',
        output_title="Paired T-Test",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Weight Time 1',
        variable_b_name='Weight Time 2',
    )
    stats_design.make_output()

def run_wilcoxon_signed_ranks(csv_file_path):
    stats_design = WilcoxonSignedRanksDesign(
        csv_file_path=csv_file_path,
        output_file_path=output_folder / 'demo_wilcoxon_signed_ranks.html',
        output_title="Wilcoxon Signed Ranks",
        show_in_web_browser=True,
        style_name='default',
        variable_a_name='Weight Time 1',
        variable_b_name='Weight Time 2',
        show_workings=True,
    )
    stats_design.make_output()

if __name__ == '__main__':
    con = sqlite.connect(sqlite_demo_db_file_path)
    cur = con.cursor()

    run_anova(people_csv_file_path)
    run_chi_square(people_csv_file_path)
    run_kruskal_wallis_h(people_csv_file_path)
    run_mann_whitney_u(people_csv_file_path)
    run_normality(people_csv_file_path)
    run_pearsons_r(people_csv_file_path)
    run_spearmans_r(people_csv_file_path)
    run_ttest_indep(people_csv_file_path)
    run_t_test_paired(people_csv_file_path)
    run_wilcoxon_signed_ranks(people_csv_file_path)

    cur.close()
    con.close()
