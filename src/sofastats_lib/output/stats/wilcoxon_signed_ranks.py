from dataclasses import dataclass
from functools import partial

import jinja2
import pandas as pd

from sofastats_lib.data_extraction.utils import get_paired_data
from sofastats_lib.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign, add_from_parent)
from sofastats_lib.output.stats.msgs import WILCOXON_VARIANCE_BY_APP_EXPLAIN
from sofastats_lib.output.styles.interfaces import StyleSpec
from sofastats_lib.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats_lib.output.utils import get_p_explain
from sofastats_lib.stats_calc.engine import (wilcoxon_signed_ranks_indiv_comparisons as wilcoxon_signed_ranks_for_workings,
    wilcoxont as wilcoxon_signed_ranks_stats_calc, )
from sofastats_lib.stats_calc.interfaces import (NumericNonParametricSampleSpecFormatted, Sample,
    WilcoxonSignedRanksResult, WilcoxonIndivComparisonResult)
from sofastats_lib.utils.maths import format_num
from sofastats_lib.utils.misc import pluralise_with_s, todict
from sofastats_lib.utils.stats import get_p_str

MAX_WORKED_DISPLAY_ROWS = 50

def wilcoxon_signed_ranks_r_from_df(df: pd.DataFrame) -> WilcoxonSignedRanksResult:
    """
    Are variables A and B correlated?

    Args:
        df: first and second col must have floats
    """
    df.columns = ['a', 'b']
    sample_a = Sample(lbl='A', vals=list(df['a']))
    sample_b = Sample(lbl='B', vals=list(df['b']))
    stats_result = wilcoxon_signed_ranks_stats_calc(sample_a=sample_a, sample_b=sample_b)
    return stats_result

@dataclass(frozen=True)
class Result(WilcoxonSignedRanksResult):
    worked_example: str

def get_worked_example(result: WilcoxonIndivComparisonResult, style_name_hyphens: str) -> str:
    row_or_rows_str = partial(pluralise_with_s, singular_word='row')
    css_first_row_var = f"firstrowvar-{style_name_hyphens}"
    html = []
    html.append(f"""
    <hr>
    <h2>Worked Example of Key Calculations</h2>
    <h3>Step 1 - Get differences</h3>""")
    html.append(f"""<table>
    <thead>
        <tr>
            <th class='{css_first_row_var}'>{result.label_a}</th>
            <th class='{css_first_row_var}'>{result.label_b}</th>
            <th class='{css_first_row_var}'>Difference</th>
        </tr>
    </thead>
    <tbody>""")
    for diff_spec in result.diff_specs[:MAX_WORKED_DISPLAY_ROWS]:
        html.append(f"""
        <tr>
            <td>{diff_spec.a}</td>
            <td>{diff_spec.b}</td>
            <td>{diff_spec.diff}</td>
        </tr>""")
    displayed_difference_from_total = len(result.diff_specs) - MAX_WORKED_DISPLAY_ROWS
    if displayed_difference_from_total > 0:
        html.append(f"""
        <tr><td colspan="3">{format_num(displayed_difference_from_total)}
        {row_or_rows_str(n_items=displayed_difference_from_total)} not displayed</td></tr>""")
    html.append("""\
        </tbody></table>
        <h3>Step 2 - Sort non-zero differences by absolute value and rank</h3>
        <p>Rank such that all examples of a value get the mean rank for all
        items of that value</p>""")
    html.append(f"""<table>
    <thead>
        <tr>
            <th class='{css_first_row_var}'>Difference</th>
            <th class='{css_first_row_var}'>Absolute Difference</th>
            <th class='{css_first_row_var}'>Counter</th>
            <th class='{css_first_row_var}'>Rank<br>(on Abs Diff)</th>
        </tr>
    </thead>
    <tbody>""")
    for ranking_spec in result.ranking_specs[:MAX_WORKED_DISPLAY_ROWS]:
        html.append(f"""
            <tr>
                <td>{ranking_spec.diff}</td>
                <td>{ranking_spec.abs_diff}</td>
                <td>{ranking_spec.counter}</td>
                <td>{ranking_spec.rank}</td>
            </tr>""")
    displayed_difference_from_total = len(result.ranking_specs) - MAX_WORKED_DISPLAY_ROWS
    if displayed_difference_from_total > 0:
        html.append(f"""
            <tr><td colspan="4">{format_num(displayed_difference_from_total)}
            {row_or_rows_str(n_items=displayed_difference_from_total)} not displayed</td></tr>""")
    html.append("""
        </tbody></table>
        <h3>Step 3 - Sum ranks for positive differences</h3>""")
    plus_rank_vals2add = [format_num(x) for x in result.plus_ranks[:MAX_WORKED_DISPLAY_ROWS]]
    displayed_difference_from_total = len(result.plus_ranks) - MAX_WORKED_DISPLAY_ROWS
    if displayed_difference_from_total > 0:
        plus_rank_vals2add.append(f'{format_num(displayed_difference_from_total)} other values not displayed')
    html.append('<p>' + ' + '.join(plus_rank_vals2add) + f' = <strong>{format_num(result.sum_plus_ranks)}</strong></p>')
    html.append("<h3>Step 4 - Sum ranks for negative differences</h3>")
    minus_rank_vals2add = [format_num(x) for x in result.minus_ranks[:MAX_WORKED_DISPLAY_ROWS]]
    displayed_difference_from_total = (len(result.minus_ranks) - MAX_WORKED_DISPLAY_ROWS)
    if displayed_difference_from_total > 0:
        minus_rank_vals2add.append(f"{format_num(displayed_difference_from_total)} other values not displayed")
    html.append(
        '<p>' + ' + '.join(minus_rank_vals2add) + f' = <strong>{format_num(result.sum_minus_ranks)}</strong></p>')
    html.append("<h3>Step 5 - Get smallest of sums for positive or negative ranks</h3>")
    html.append(f"<p>The lowest value of {format_num(result.sum_plus_ranks)} and {format_num(result.sum_minus_ranks)} "
        f"is {format_num(result.t)} so Wilcoxon's T statistic is <strong>{format_num(result.t)}</strong></p>")
    html.append("<h3>Step 6 - Get count of all non-zero diffs</h3>")
    html.append(
        f"<p>Just the number of records in the table from Step 2 i.e. <strong>{format_num(result.n)}</strong></p>")
    html.append(
        "<p>The only remaining question is the probability of a sum as large as that observed (T) for a given N value. "
        "The smaller the N and the bigger the T the less likely the difference "
        f'between "{result.label_a}" and "{result.label_b}" could occur by chance.</p>')
    return '\n'.join(html)

def get_html(result: Result, style_spec: StyleSpec, *, dp: int) -> str:
    tpl = """\
    <style>
        {{ generic_unstyled_css }}
        {{ styled_stats_tbl_css }}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>

    <p>p value: {{ p }}<a class='tbl-heading-footnote' href='#ft1'><sup>1</sup></a></p>
    <p>t statistic: {{ t }}</p>
    <p>Degrees of Freedom (df): {{ degrees_of_freedom }}</p>

   <h3>Group summary details</h3>
    <table cellspacing='0'>
      <thead>
        <tr>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Group</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>N</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Median</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Min</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Max</th>
        </tr>
      </thead>
      <tbody>
        {% for group_spec in group_specs %}
          <tr>
            <td class='lbl-{{ style_name_hyphens }}'>{{group_spec.lbl}}</td>
            <td class='right'>{{ group_spec.n }}</td>
            <td class='right'>{{ group_spec.median }}</td>
            <td class='right'>{{ group_spec.sample_min }}</td>
            <td class='right'>{{ group_spec.sample_max }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup>{{ loop.index }}</sup>{{ footnote }}</p>
    {% endfor %}

    {% if worked_example %}
      {{ worked_example }}
    {% endif %}

    </div>
    """
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    title = f'Results of Wilcoxon Signed Ranks Test of "{result.group_a_spec.lbl}" vs "{result.group_b_spec.lbl}"'
    num_tpl = f"{{:,.{dp}f}}"  ## use comma as thousands separator, and display specified decimal places
    ## format group details needed by second table
    formatted_group_specs = []
    for orig_group_spec in [result.group_a_spec, result.group_b_spec]:
        n = format_num(orig_group_spec.n)
        sample_median = num_tpl.format(round(orig_group_spec.median, dp))
        formatted_group_spec = NumericNonParametricSampleSpecFormatted(
            lbl=orig_group_spec.lbl,
            n=n,
            median=sample_median,
            sample_min=str(orig_group_spec.sample_min),
            sample_max=str(orig_group_spec.sample_max),
        )
        formatted_group_specs.append(formatted_group_spec)
    lbl_a = result.group_a_spec.lbl
    lbl_b = result.group_b_spec.lbl
    p_explain = get_p_explain(lbl_a, lbl_b)
    two_tailed_explanation = (
        "This is a two-tailed result i.e. based on the likelihood of a difference "
        f'where the direction ("{lbl_a}" higher than "{lbl_b}" or "{lbl_b}" higher than "{lbl_a}") '
        "doesn't matter.")
    p_full_explanation = f"{p_explain}</br></br>{two_tailed_explanation}"

    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'style_name_hyphens': style_spec.style_name_hyphens,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'footnotes': [p_full_explanation, WILCOXON_VARIANCE_BY_APP_EXPLAIN, ],
        'group_specs': formatted_group_specs,
        'p': get_p_str(result.p),
        't': round(result.t, dp),
        'worked_example': result.worked_example,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@add_from_parent
@dataclass(frozen=False)
class WilcoxonSignedRanksDesign(CommonDesign):
    variable_a_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    variable_b_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    style_name: str = 'default'
    decimal_points: int = 3
    show_workings: bool = False

    def to_result(self) -> WilcoxonSignedRanksResult:
        ## labels
        variable_a_label = self.data_labels.var2var_lbl.get(self.variable_a_name, self.variable_a_name)
        variable_b_label = self.data_labels.var2var_lbl.get(self.variable_b_name, self.variable_b_name)
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_a_label=variable_a_label,
            variable_b_name=self.variable_b_name, variable_b_label=variable_b_label,
            tbl_filt_clause=self.table_filter)
        stats_result = wilcoxon_signed_ranks_stats_calc(
            sample_a=paired_data.sample_a, sample_b=paired_data.sample_b, high_volume_ok=False)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## labels
        variable_a_label = self.data_labels.var2var_lbl.get(self.variable_a_name, self.variable_a_name)
        variable_b_label = self.data_labels.var2var_lbl.get(self.variable_b_name, self.variable_b_name)
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_a_label=variable_a_label,
            variable_b_name=self.variable_b_name, variable_b_label=variable_b_label,
            tbl_filt_clause=self.table_filter)
        stats_result = wilcoxon_signed_ranks_stats_calc(
            sample_a=paired_data.sample_a, sample_b=paired_data.sample_b, high_volume_ok=False)

        if self.show_workings:
            result_workings = wilcoxon_signed_ranks_for_workings(
                sample_a=paired_data.sample_a, sample_b=paired_data.sample_b,
                label_a=variable_a_label, label_b=variable_b_label)
            worked_example = get_worked_example(result_workings, style_spec.style_name_hyphens)
        else:
            worked_example = ''

        result = Result(**todict(stats_result),
            worked_example=worked_example,
        )
        html = get_html(result, style_spec, dp=self.decimal_points)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
