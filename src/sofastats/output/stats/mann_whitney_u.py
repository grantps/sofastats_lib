from dataclasses import dataclass
from functools import partial
from typing import Any

import jinja2
import pandas as pd

from sofastats.data_extraction.interfaces import ValFilterSpec
from sofastats.data_extraction.utils import get_sample
from sofastats.output.interfaces import DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType
from sofastats.output.stats.interfaces import CommonStatsDesignWithoutSortAttributes
from sofastats.output.stats.msgs import P_EXPLAIN_TWO_GROUPS
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats.output.utils import get_p_explain
from sofastats.stats_calc.engine import (mann_whitney_u as mann_whitney_u_stats_calc,
    mann_whitney_u_indiv_comparisons as mann_whitney_u_for_workings)
from sofastats.stats_calc.interfaces import (
    MannWhitneyUResult, MannWhitneyUIndivComparisonsResult, NumericNonParametricSampleSpecFormatted, Sample)
from sofastats.stats_calc.utils import get_samples_from_df
from sofastats.utils.maths import format_num, is_numeric
from sofastats.utils.misc import pluralise_with_s, todict
from sofastats.utils.stats import get_p_str

MAX_WORKED_DISPLAY_ROWS = 50

def mann_whitney_u_from_df(df: pd.DataFrame) -> MannWhitneyUResult:
    """
    Does group A have a different average metric value from group B?

    Args:
        df: first col must have two values, one for each group, and the second col must have floats
    """
    samples = get_samples_from_df(df, n_expected_groups=2)
    sample_a, sample_b = samples
    stats_result = mann_whitney_u_stats_calc(sample_a=sample_a, sample_b=sample_b, high_volume_ok=False)
    return stats_result

@dataclass(frozen=True)
class Result(MannWhitneyUResult):
    grouping_field_name: str
    measure_field_name: str
    sample_a: Sample
    sample_b: Sample
    n_a: int
    n_b: int
    even_matches: float
    worked_example: str
    decimal_points: int = 3

def get_worked_example(result: MannWhitneyUIndivComparisonsResult, style_name_hyphens: str) -> str:
    row_or_rows_str = partial(pluralise_with_s, singular_word='row')
    css_first_row_var = f"firstrowvar-{style_name_hyphens}"
    html = []
    html.append(f"""
    <hr>
    <h2>Worked Example of Key Calculations</h2>
    <p>Note - the method shown below is based on ranked values of the data as a whole, not on every possible comparison
    - but the result is exactly the same. Working with ranks is much more efficient.</p>
    <h3>Step 1 - Add ranks to all values</h3>
    <p>Note on ranking - rank such that all examples of a value get the median rank for all items of that value.</p>
    <p>If calculating by hand, and one sample is shorter than the others,
    make that the first sample to reduce the number of calculations</p>
    <p>For the rest of this worked example, sample 1 is "{result.label_1}" and sample 2 is {result.label_2}".""")
    html.append(f"""<table>
    <thead>
        <tr>
            <th class='{css_first_row_var}'>Sample</th>
            <th class='{css_first_row_var}'>Value</th>
            <th class='{css_first_row_var}'>Counter</th>
            <th class='{css_first_row_var}'>Rank</th>
        </tr>
    </thead>
    <tbody>""")
    for mw_val in result.mw_vals[:MAX_WORKED_DISPLAY_ROWS]:
        html.append(f"""
        <tr>
            <td>{mw_val.sample}</td>
            <td>{mw_val.val}</td>
            <td>{mw_val.counter}</td>
            <td>{mw_val.rank}</td>
        </tr>""")
    diff = len(result.mw_vals) - MAX_WORKED_DISPLAY_ROWS
    if diff > 0:
        html.append(f"""
        <tr><td colspan="4">{format_num(diff)} {row_or_rows_str(n_items=diff)}
        not displayed</td></tr>""")
    html.append("""
    </tbody>
    </table>""")
    html.append('<h3>Step 2 - Sum the ranks for sample 1</h3>')
    val_1s2add = [str(x)
        for x in result.ranks_1[:MAX_WORKED_DISPLAY_ROWS]]
    diff_ranks_1 = result.n_1 - MAX_WORKED_DISPLAY_ROWS
    if diff_ranks_1 > 0:
        val_1s2add.append(
            f'{format_num(diff_ranks_1)} other values not displayed')
    sum_rank_1 = format_num(result.sum_rank_1)
    html.append('<p>sum_ranks<sub>1</sub> = ' + ' + '.join(val_1s2add) + f' i.e. <strong>{sum_rank_1}</strong></p>')
    html.append("""<h3>Step 3 - Calculate U for sample 1 as per:</h3>
    <p>
        u<sub>1</sub> = n<sub>1</sub>*n<sub>2</sub> + ((n<sub>1</sub>*(n<sub>1</sub> + 1))/2.0) - sum_ranks<sub>1</sub>
    </p>""")
    n_1 = format_num(result.n_1)
    n_2 = format_num(result.n_2)
    u_1 = format_num(result.u_1)
    u_2 = format_num(result.u_2)
    u_val = format_num(result.u)
    html.append(f"""<p>u<sub>1</sub> = {n_1}*{n_2} + ({n_1}*({n_2}+1))/2 -
    {sum_rank_1} i.e. <strong>{u_1}</strong></p>""")
    html.append(f"""<h3>Step 4 - Calculate U for sample 2 as per:</h3>
    <p>u<sub>2</sub> = n<sub>1</sub>*n<sub>2</sub> - u<sub>1</sub></p>""")
    html.append(f"""<p>u<sub>2</sub> = {n_1}*{n_2} - {u_1} i.e. <strong>{u_2}</strong></p>""")
    html.append(f"""<h3>Step 5 - Identify the lowest of the U values</h3>
    <p>The lowest value of {u_1} and {u_2} is <strong>{u_val}</strong></p>""")
    html.append("""<p>After this, you would use the N values and other methods
    to see if the value for U is likely to happen by chance
    but that is outside of the scope of this worked example.</p>""")
    return '\n'.join(html)

def get_html(result: Result, style_spec: StyleSpec) -> str:
    tpl = """\
    <style>
        {{ generic_unstyled_css }}
        {{ styled_stats_tbl_css }}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>

    <p>Two-tailed p value: {{ p_str }} <a href='#ft1'><sup>1</sup></a></p>
    <p>U statistic: {{ u }} <a href='#ft2'><sup>2</sup></a></p>
    <p>z: {{ z }}</p>
    
    <h3>Group summary details</h3>
    <table cellspacing='0'>
      <thead>
        <tr>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Group</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>N</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Median</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Avg Rank</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Min</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Max</th>
        </tr>
      </thead>
      <tbody>
        {% for group_spec in group_specs %}
          <tr>
            <td class='lbl-{{ style_name_hyphens }}'>{{group_spec.label}}</td>
            <td class='right'>{{ group_spec.n }}</td>
            <td class='right'>{{ group_spec.median }}</td>
            <td class='right'>{{ group_spec.avg_rank }}</td>
            <td class='right'>{{ group_spec.sample_min }}</td>
            <td class='right'>{{ group_spec.sample_max }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup style='color: {{footnote_font_color}};'>{{ loop.index }}</sup>&nbsp;{{ footnote }}</p>
    {% endfor %}

    {% if worked_example %}
      {{ worked_example }}
    {% endif %}

    </div>
    """
    dp = result.decimal_points
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    title = (f'Results of Mann-Whitney U Test of "{result.measure_field_name}" '
        f'''for "{result.grouping_field_name}" groups "{result.group_a_spec.label}" and "{result.group_b_spec.label}"''')

    label_a = result.group_a_spec.label
    label_b = result.group_b_spec.label

    p_explain = get_p_explain(label_a, label_b)
    two_tailed_explanation = (
        "This is a two-tailed result i.e. based on the likelihood of a difference "
        f'where the direction ("{label_a}" higher than "{label_b}" or "{label_b}" higher than "{label_a}") '
        "doesn't matter.")
    p_full_explanation = f"{p_explain}</br></br>{two_tailed_explanation}"

    u_statistic_explain = ("U is based on the results of matches "
    f'between the "{label_a}" and "{label_b}" groups. '
    f'In each match,<br>the winner is the one with the highest "{result.measure_field_name}" '
    "(in a draw, each group gets half a point which is<br>why U can sometimes end in .5). "
    "The further the number is away from an even result"
    "<br>i.e. half the number of possible matches "
    f"(i.e. half of {result.n_a} x {result.n_b} in this case i.e. {result.even_matches})"
    "<br>the more unlikely the difference is by chance alone and the more statistically significant it is.")

    num_tpl = f"{{:,.{dp}f}}"  ## use comma as thousands separator, and display specified decimal places
    ## format group details needed by second table
    formatted_group_specs = []
    for orig_group_spec in [result.group_a_spec, result.group_b_spec]:
        n = format_num(orig_group_spec.n)
        sample_median = num_tpl.format(round(orig_group_spec.median, dp))
        avg_rank = num_tpl.format(round(orig_group_spec.avg_rank, dp))
        formatted_group_spec = NumericNonParametricSampleSpecFormatted(
            label=orig_group_spec.label,
            n=n,
            median=sample_median,
            sample_min=str(orig_group_spec.sample_min),
            sample_max=str(orig_group_spec.sample_max),
            avg_rank=avg_rank,
        )
        formatted_group_specs.append(formatted_group_spec)

    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'style_name_hyphens': style_spec.style_name_hyphens,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'footnote_font_color': style_spec.table.footnote_font_color,
        'footnotes': [p_full_explanation, u_statistic_explain],
        'group_specs': formatted_group_specs,
        'p_explain_two_groups': P_EXPLAIN_TWO_GROUPS,
        'p_str': get_p_str(result.p * 2),  ## double one-tailed p value so can report two-tailed result
        'u': result.small_u,
        'worked_example': result.worked_example,
        'z': round(result.z, dp),
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@dataclass(frozen=False)
class MannWhitneyUDesign(CommonStatsDesignWithoutSortAttributes):
    """
    Args:
        measure_field_name: the name of the field aggregated by group - the analysis compares the mean value of each group.
            For example, 'Age'
        grouping_field_name: the name of the field used to define the groups compared in the analysis e.g. 'Country'
        group_a_value: the analysis will compare the ranks of this group
            against the ranks of the group defined by group_b_value
        group_b_value: the analysis will compare the ranks of this group
            against the ranks of the group defined by group_a_value
        show_workings: show the workings so you can see how the final results were derived
    """
    measure_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    grouping_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_a_value: Any = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_b_value: Any = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    show_workings: bool = False

    def to_result(self) -> MannWhitneyUResult:
        ## build samples ready for mann whitney u function
        grouping_filter_a = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_a_value, val_is_numeric=is_numeric(self.group_a_value))
        sample_a = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filter=grouping_filter_a, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        grouping_filter_b = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_b_value, val_is_numeric=is_numeric(self.group_b_value))
        sample_b = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filter=grouping_filter_b, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        stats_result = mann_whitney_u_stats_calc(sample_a=sample_a, sample_b=sample_b, high_volume_ok=False)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        ## build samples ready for mann whitney u function
        grouping_filter_a = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_a_value, val_is_numeric=is_numeric(self.group_a_value))
        sample_a = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filter=grouping_filter_a, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        grouping_filter_b = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_b_value, val_is_numeric=is_numeric(self.group_b_value))
        sample_b = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filter=grouping_filter_b, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        ## get result
        stats_result = mann_whitney_u_stats_calc(sample_a=sample_a, sample_b=sample_b, high_volume_ok=False)
        n_a = stats_result.group_a_spec.n
        n_b = stats_result.group_b_spec.n
        even_matches = (n_a * n_b) / float(2)

        if self.show_workings:
            result_workings = mann_whitney_u_for_workings(sample_a=sample_a, sample_b=sample_b, high_volume_ok=False)
            worked_example = get_worked_example(result_workings, style_spec.style_name_hyphens)
        else:
            worked_example = ''

        result = Result(**todict(stats_result),
            sample_a=sample_a,
            sample_b=sample_b,
            grouping_field_name=self.grouping_field_name,
            measure_field_name=self.measure_field_name,
            n_a=n_a,
            n_b=n_b,
            even_matches=even_matches,
            worked_example=worked_example,
            decimal_points=self.decimal_points,
        )
        html = get_html(result, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            output_item_type=OutputItemType.STATS,
            output_title=self.output_title,
            design_name=self.__class__.__name__,
            style_name=self.style_name,
        )

# if __name__ == '__main__':
#     from random import randint
#     data_a = [('A', randint(1, 100)) for _i in range(100)]
#     data_b = [('B', 1.5 * randint(1, 100)) for _i in range(100)]
#     data = data_a + data_b
#     df = pd.DataFrame(data)
#     print(mann_whitney_u_from_df(df))
