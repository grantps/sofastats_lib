from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import jinja2
import pandas as pd

from sofastats.data_extraction.interfaces import ValFilterSpec
from sofastats.data_extraction.utils import get_sample
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.stats.msgs import (
    ONE_TAIL_EXPLAIN, ONE_TAILED_EXPLANATION, P_EXPLAIN_MULTIPLE_GROUPS, P_EXPLANATION_WHEN_MULTIPLE_GROUPS)
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats.output.utils import get_p_explain
from sofastats.stats_calc.engine import kruskalwallish as kruskal_wallis_h_stats_calc
from sofastats.stats_calc.interfaces import KruskalWallisHResult, NumericNonParametricSampleSpecFormatted
from sofastats.stats_calc.utils import get_samples_from_df
from sofastats.utils.maths import format_num, is_numeric
from sofastats.utils.misc import apply_custom_sorting_to_values, todict
from sofastats.utils.stats import get_p_str

def kruskal_wallis_h_from_df(df: pd.DataFrame) -> KruskalWallisHResult:
    """
    Do different groups have different average metric values?

    Args:
        df: first col must have one value for each group, and the second col must have floats
    """
    samples = get_samples_from_df(df)
    stats_result = kruskal_wallis_h_stats_calc(samples=samples)
    return stats_result

@dataclass(frozen=True)
class Result(KruskalWallisHResult):
    grouping_field_name: str
    measure_field_name: str

def get_html(result: Result, style_spec: StyleSpec, *, dp: int) -> str:
    tpl = """\
    <style>
        {{ generic_unstyled_css }}
        {{ styled_stats_tbl_css }}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>

    <p>p value: {{ p }}<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft1'><sup>1</sup></a></p>
    <p>Kruskal-Wallis H statistic: {{ h }}</p>
    <p>Degrees of Freedom (df): {{ degrees_of_freedom }}</p>
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

    <p><a id='ft1'></a><sup>1</sup>{{ p_explain_multiple_groups }}<br><br>{{one_tail_explain}}</p>

    <p>No worked example available for this test</p>

    </div>
    """
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    group_val_labels = [group_spec.label for group_spec in result.group_specs]
    if len(group_val_labels) < 2:
        raise Exception(f"Expected multiple groups in Kruskal-Wallis analysis. Details:\n{result}")
    group_a_label = group_val_labels[0]
    group_b_label = group_val_labels[-1]
    title = (f'Results of Kruskal-Wallis H test of average "{result.measure_field_name}" '
        f'for "{result.grouping_field_name}" groups from "{group_a_label}" to "{group_b_label}"')
    p_explain = get_p_explain(group_a_label, group_b_label)
    p_full_explanation = f"{p_explain}</br></br>{ONE_TAILED_EXPLANATION}"
    formatted_group_specs = []
    num_tpl = f"{{:,.{dp}f}}"  ## use comma as thousands separator, and display specified decimal places
    for orig_group_spec in result.group_specs:
        n = format_num(orig_group_spec.n)
        formatted_group_spec = NumericNonParametricSampleSpecFormatted(
            label=orig_group_spec.label,
            n=n,
            median=num_tpl.format(round(orig_group_spec.median, dp)),
            sample_min=num_tpl.format(round(orig_group_spec.sample_min, dp)),
            sample_max=num_tpl.format(round(orig_group_spec.sample_max, dp)),
        )
        formatted_group_specs.append(formatted_group_spec)
    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'style_name_hyphens': style_spec.style_name_hyphens,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'degrees_of_freedom': result.degrees_of_freedom,
        'footnotes': [p_full_explanation, P_EXPLANATION_WHEN_MULTIPLE_GROUPS, ],
        'group_specs': formatted_group_specs,
        'h': round(result.h, dp),
        'one_tail_explain': ONE_TAIL_EXPLAIN,
        'p': get_p_str(result.p),
        'p_explain_multiple_groups': P_EXPLAIN_MULTIPLE_GROUPS,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@dataclass(frozen=False)
class KruskalWallisHDesign(CommonDesign):
    measure_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    grouping_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_values: Sequence[Any] = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    style_name: str = 'default'
    decimal_points: int = 3
    show_workings: bool = False

    def to_result(self) -> KruskalWallisHResult:
        ## values (sorted)
        grouping_field_values = apply_custom_sorting_to_values(
            variable_name=self.grouping_field_name, values=list(self.group_values), sort_orders=self.sort_orders)
        ## data
        grouping_val_is_numeric = all(is_numeric(x) for x in self.group_values)
        samples = []
        for grouping_field_value in grouping_field_values:
            grouping_filter = ValFilterSpec(variable_name=self.grouping_field_name, value=grouping_field_value,
                val_is_numeric=grouping_val_is_numeric)
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                grouping_filt=grouping_filter, measure_field_name=self.measure_field_name,
                tbl_filt_clause=self.table_filter)
            samples.append(sample)
        stats_result = kruskal_wallis_h_stats_calc(samples)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## values (sorted)
        grouping_field_values = apply_custom_sorting_to_values(
            variable_name=self.grouping_field_name, values=list(self.group_values), sort_orders=self.sort_orders)
        ## data
        grouping_val_is_numeric = all(is_numeric(x) for x in self.group_values)
        samples = []
        for grouping_field_value in grouping_field_values:
            grouping_filter = ValFilterSpec(variable_name=self.grouping_field_name, value=grouping_field_value,
                val_is_numeric=grouping_val_is_numeric)
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                grouping_filt=grouping_filter, measure_field_name=self.measure_field_name,
                tbl_filt_clause=self.table_filter)
            samples.append(sample)
        stats_result = kruskal_wallis_h_stats_calc(samples)
        result = Result(**todict(stats_result),
            grouping_field_name=self.grouping_field_name,
            measure_field_name=self.measure_field_name,
        )
        html = get_html(result, style_spec, dp=self.decimal_points)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
