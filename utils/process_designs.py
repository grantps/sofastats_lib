## To run the demo examples, install the sofastats_examples package
## and run the functions inside e.g. simple_bar_chart_from_sqlite_db() in demo_charts.py
from itertools import chain
import sqlite3 as sqlite

from webbrowser import open_new_tab

from sofastats.output.interfaces import ReportDesignsSpec
from sofastats.output.utils import get_gallery_report, get_report

from sofastats_examples.scripts.conf import (education_csv_file_path, output_folder, people_csv_file_path,
    sports_csv_file_path, sqlite_demo_db_file_path)
import sofastats_examples.scripts.demo_charts as charts
import sofastats_examples.scripts.demo_stats as stats
import sofastats_examples.scripts.demo_tables as tables

def run(*, do_charts=False, do_stats=False, show_stats_results=False, do_tables=False,
        make_separate_output=False,
        make_combined_output=False,
        combined_output_report_name: str | None = None, combined_output_report_title: str | None = None,
        is_gallery=False):
    if make_combined_output and (combined_output_report_name is None or combined_output_report_title is None):
        raise Exception(f"If making a combined report you must supply a file name and (HTML) title")
    con = sqlite.connect(sqlite_demo_db_file_path)
    cur = con.cursor()

    report_designs_specs: list[ReportDesignsSpec] = []

    if do_charts:
        chart_designs = []

        chart_designs.append(charts.simple_bar_chart_from_sqlite_db(cur))
        chart_designs.append(charts.simple_bar_chart_from_csv(people_csv_file_path))
        chart_designs.append(charts.simple_bar_chart_percents_from_csv(people_csv_file_path))
        chart_designs.append(charts.simple_bar_chart_averages_from_csv(people_csv_file_path))
        chart_designs.append(charts.simple_bar_chart_sums_from_csv(people_csv_file_path))
        chart_designs.append(charts.simple_bar_chart_lots_of_x_vals(people_csv_file_path))
        chart_designs.append(charts.multi_bar_chart(people_csv_file_path))
        chart_designs.append(charts.clustered_bar_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_clustered_bar_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_clustered_percents_bar_chart(people_csv_file_path))

        chart_designs.append(charts.line_chart(people_csv_file_path))
        chart_designs.append(charts.line_chart_time_series(people_csv_file_path))
        chart_designs.append(charts.line_chart_time_series_rotated_labels(people_csv_file_path))
        chart_designs.append(charts.multi_line_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_line_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_multi_line_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_multi_line_chart_time_series(people_csv_file_path))

        chart_designs.append(charts.area_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_area_chart(people_csv_file_path))

        chart_designs.append(charts.pie_chart(sports_csv_file_path))
        chart_designs.append(charts.multi_chart_pie_chart(sports_csv_file_path))

        chart_designs.append(charts.simple_scatter_plot(education_csv_file_path))
        chart_designs.append(charts.by_series_scatter_plot(education_csv_file_path))
        chart_designs.append(charts.multi_chart_scatter_plot(education_csv_file_path))
        chart_designs.append(charts.multi_chart_by_series_scatter_plot(education_csv_file_path))

        chart_designs.append(charts.histogram_chart(people_csv_file_path))
        chart_designs.append(charts.multi_chart_histogram(people_csv_file_path))

        chart_designs.append(charts.simple_box_plot(people_csv_file_path))
        chart_designs.append(charts.box_plot_narrow_labels(people_csv_file_path))
        chart_designs.append(charts.box_plot_very_wide(people_csv_file_path))
        chart_designs.append(charts.clustered_box_plot_default_style(people_csv_file_path))
        chart_designs.append(charts.clustered_box_plot_black_pastel_style(people_csv_file_path))

        report_designs_specs.append(ReportDesignsSpec(title="Charts", designs=chart_designs))

    if do_tables:
        table_designs = []

        table_designs.append(tables.cross_tab_from_sqlite_db_filtered(cur))
        table_designs.append(tables.cross_tab_from_sqlite_db(cur))
        table_designs.append(tables.cross_tab(people_csv_file_path))
        table_designs.append(tables.repeat_level_two_row_var_cross_tab(people_csv_file_path))
        table_designs.append(tables.simple_freq_tbl(people_csv_file_path))

        report_designs_specs.append(ReportDesignsSpec(title="Report Tables", designs=table_designs))
    if do_stats:
        stats_designs = []

        stats_designs.append(stats.anova_black_pastel_style(people_csv_file_path))
        stats_designs.append(stats.anova_red_spirals_style(people_csv_file_path))
        stats_designs.append(stats.chi_square(people_csv_file_path))
        stats_designs.append(stats.kruskal_wallis_h(people_csv_file_path))
        stats_designs.append(stats.mann_whitney_u(people_csv_file_path))
        stats_designs.append(stats.normality(people_csv_file_path))
        stats_designs.append(stats.pearsons_r(people_csv_file_path))
        stats_designs.append(stats.spearmans_r(people_csv_file_path))
        stats_designs.append(stats.independent_t_test(people_csv_file_path))
        stats_designs.append(stats.paired_t_test(people_csv_file_path))
        stats_designs.append(stats.wilcoxon_signed_ranks(people_csv_file_path))

        if show_stats_results:
            for stats_design in stats_designs:
                print(stats_design.to_result())

        report_designs_specs.append(ReportDesignsSpec(title="Statistical Tests", designs=stats_designs))

    if make_separate_output:
        for report_designs_spec in report_designs_specs:
            for design in report_designs_spec.designs:
                design.make_output()
    if make_combined_output:
        if is_gallery:
            report = get_gallery_report(report_designs_specs=report_designs_specs, title=combined_output_report_title)
        else:
            designs = list(chain(*[report_designs_spec.designs for report_designs_spec in report_designs_specs]))
            report = get_report(designs=designs, title=combined_output_report_title)
        fpath = output_folder / f"{combined_output_report_name}.html"
        report.to_file(fpath)
        open_new_tab(url=f"file://{fpath}")

    cur.close()
    con.close()

if __name__ == '__main__':
    pass
    # run(do_charts=True, do_stats=True, do_tables=True, make_separate_output=True, make_combined_output=False)
