from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any

import jinja2
import pandas as pd

from sofastats.data_extraction.interfaces import ValFilterSpec, ValSpec
from sofastats.data_extraction.utils import get_sample
from sofastats.output.charts import mpl_pngs
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign, add_from_parent)
from sofastats.output.stats.common import get_embedded_histogram_html
from sofastats.output.stats.msgs import (
    CI_EXPLAIN, KURTOSIS_EXPLAIN,
    NORMALITY_MEASURE_EXPLAIN, OBRIEN_EXPLAIN, ONE_TAIL_EXPLAIN,
    P_EXPLAIN_MULTIPLE_GROUPS,
    SKEW_EXPLAIN, STD_DEV_EXPLAIN,
)
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats.stats_calc.engine import anova as anova_stats_calc
from sofastats.stats_calc.interfaces import AnovaResult, NumericParametricSampleSpecFormatted
from sofastats.stats_calc.utils import get_samples_from_df
from sofastats.utils.maths import format_num, is_numeric
from sofastats.utils.misc import todict
from sofastats.utils.stats import get_p_str

def anova_from_df(df: pd.DataFrame, *,
        grouping_field_label: str = 'Grouping Field', measure_field_label: str = 'Measure Field',
        high_precision_required=False) -> AnovaResult:
    """
    Do different groups have different average metric values?

    Args:
        df: first col must have one value for each group, and the second col must have floats
    """
    samples = get_samples_from_df(df)
    stats_result = anova_stats_calc(group_lbl=grouping_field_label, measure_fld_lbl=measure_field_label,
        samples=samples, high=high_precision_required)
    return stats_result

@dataclass(frozen=True)
class Result(AnovaResult):
    group_lbl: str
    measure_fld_lbl: str
    histograms2show: Sequence[str]

def get_html(result: Result, style_spec: StyleSpec, *, dp: int) -> str:
    tpl = """\
    <style>
        {{ generic_unstyled_css }}
        {{ styled_stats_tbl_css }}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>
    <h3>Analysis of variance table</h3>
    <table cellspacing='0'>
    <thead>
      <tr>
        <th class='firstcolvar-{{ style_name_hyphens }}'>Source</th>
        <th class='firstcolvar-{{ style_name_hyphens }}'>Sum of Squares</th>
        <th class='firstcolvar-{{ style_name_hyphens }}'>df</th>
        <th class='firstcolvar-{{ style_name_hyphens }}'>Mean Sum of Squares</th>
        <th class='firstcolvar-{{ style_name_hyphens }}'>F</th>
        <th class='firstcolvar-{{ style_name_hyphens }}'>p<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft1'><sup>1</sup></a></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class='lbl-{{ style_name_hyphens }}'>Between</td>
        <td class='right'>{{ sum_squares_between_groups }}</td>
        <td class='right'>{{ degrees_freedom_between_groups }}</td>
        <td class='right'>{{ mean_squares_between_groups }}</td>
        <td class='right'>{{ F }}</td>
        <td>{{p}}</td>
      </tr>
      <tr>
        <td class='lbl-{{ style_name_hyphens }}'>Within</td>
        <td class='right'>{{ sum_squares_within_groups }}</td>
        <td class='right'>{{ degrees_freedom_within_groups }}</td>
        <td class='right'>{{ mean_squares_within_groups }}</td>
        <td></td>
        <td></td>
      </tr>
    </tbody>
    </table>
    <p>O'Brien's test for homogeneity of variance: {{ obriens_msg }}<a href='#ft2'><sup>2</sup></a></p>
    <h3>Group summary details</h3>
    <table cellspacing='0'>
      <thead>
        <tr>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Group</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>N</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Mean</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>CI 95%<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft3'><sup>3</sup></a></th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Standard Deviation<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft4'><sup>4</sup></a></th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Min</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Max</th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Kurtosis<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft5'><sup>5</sup></a></th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>Skew<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft6'><sup>6</sup></a></th>
          <th class='firstcolvar-{{ style_name_hyphens }}'>p abnormal<a class='tbl-heading-footnote-{{ style_name_hyphens }}' href='#ft7'><sup>7</sup></a></th>
        </tr>
      </thead>
      <tbody>
        {% for group_spec in group_specs %}
          <tr>
            <td class='lbl-{{ style_name_hyphens }}'>{{ group_spec.lbl }}</td>
            <td class='right'>{{ group_spec.n }}</td>
            <td class='right'>{{ group_spec.mean }}</td>
            <td class='right'>{{ group_spec.ci95 }}</td>
            <td class='right'>{{ group_spec.stdev }}</td>
            <td class='right'>{{ group_spec.sample_min }}</td>
            <td class='right'>{{ group_spec.sample_max }}</td>
            <td class='right'>{{ group_spec.kurtosis }}</td>
            <td class='right'>{{ group_spec.skew }}</td>
            <td class='right'>{{ group_spec.p }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup>{{ loop.index }}</sup>{{ footnote }}</p>
    {% endfor %}

    {% for histogram2show in histograms2show %}
      {{ histogram2show }}  <!-- either an <img> or an error message <p> -->
    {% endfor %}

    <p>{{ workings_msg }}</p>

    </div>
    """
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    group_val_lbls = [group_spec.lbl for group_spec in result.group_specs]
    if len(group_val_lbls) < 2:
        raise Exception(f"Expected multiple groups in ANOVA. Details:\n{result}")
    labels_str = '"' + '", "'.join(group_val_lbls) + '"'
    title = (f"Results of ANOVA test of average {result.measure_fld_lbl} "
        f'for "{result.group_lbl}" groups: {labels_str}')
    num_tpl = f"{{:,.{dp}f}}"  ## use comma as thousands separator, and display specified decimal places
    ## format group details needed by second table
    formatted_group_specs = []
    mpl_pngs.set_gen_mpl_settings(axes_lbl_size=10, xtick_lbl_size=8, ytick_lbl_size=8)
    for orig_group_spec in result.group_specs:
        n = format_num(orig_group_spec.n)
        ci95_left = num_tpl.format(round(orig_group_spec.ci95[0], dp))
        ci95_right = num_tpl.format(round(orig_group_spec.ci95[1], dp))
        ci95 = f"{ci95_left} - {ci95_right}"
        std_dev = num_tpl.format(round(orig_group_spec.std_dev, dp))
        sample_mean = num_tpl.format(round(orig_group_spec.mean, dp))
        kurt = num_tpl.format(round(orig_group_spec.kurtosis, dp))
        skew_val = num_tpl.format(round(orig_group_spec.skew, dp))
        formatted_group_spec = NumericParametricSampleSpecFormatted(
            lbl=orig_group_spec.lbl,
            n=n,
            mean=sample_mean,
            ci95=ci95,
            std_dev=std_dev,
            sample_min=str(orig_group_spec.sample_min),
            sample_max=str(orig_group_spec.sample_max),
            kurtosis=kurt,
            skew=skew_val,
            p=orig_group_spec.normality_test_p,
        )
        formatted_group_specs.append(formatted_group_spec)
    p_explanation = f"{P_EXPLAIN_MULTIPLE_GROUPS}<br><br>{ONE_TAIL_EXPLAIN}"
    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'style_name_hyphens': style_spec.style_name_hyphens,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'degrees_freedom_between_groups': f"{result.degrees_freedom_between_groups:,}",
        'F': num_tpl.format(round(result.F, dp)),
        'footnotes': [p_explanation,
            OBRIEN_EXPLAIN, CI_EXPLAIN, STD_DEV_EXPLAIN, KURTOSIS_EXPLAIN, SKEW_EXPLAIN, NORMALITY_MEASURE_EXPLAIN],
        'degrees_freedom_within_groups': f"{result.degrees_freedom_within_groups:,}",
        'group_specs': formatted_group_specs,
        'histograms2show': result.histograms2show,
        'mean_squares_between_groups': num_tpl.format(round(result.mean_squares_between_groups, dp)),
        'mean_squares_within_groups': num_tpl.format(round(result.mean_squares_within_groups, dp)),
        'obriens_msg': result.obriens_msg,
        'p': get_p_str(result.p),
        'sum_squares_between_groups': num_tpl.format(round(result.sum_squares_between_groups, dp)),
        'sum_squares_within_groups': num_tpl.format(round(result.sum_squares_within_groups, dp)),
        'workings_msg': "No worked example available for this test",
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@add_from_parent
@dataclass(frozen=False)
class AnovaDesign(CommonDesign):
    measure_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    grouping_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_values: Collection[Any] = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    style_name: str = 'default'
    high_precision_required: bool = False
    decimal_points: int = 3

    def to_result(self) -> AnovaResult:
        ## labels
        grouping_fld_lbl = self.data_labels.var2var_lbl.get(self.grouping_field_name, self.grouping_field_name)
        measure_fld_lbl = self.data_labels.var2var_lbl.get(self.measure_field_name, self.measure_field_name)
        val2lbl = self.data_labels.var2val2lbl.get(self.grouping_field_name, {})
        grouping_fld_vals_spec = list({
            ValSpec(val=group_val, lbl=val2lbl.get(group_val, str(group_val))) for group_val in self.group_values})
        grouping_fld_vals_spec.sort(key=lambda vs: vs.lbl)
        ## data
        grouping_val_is_numeric = all(is_numeric(x) for x in self.group_values)
        ## build sample results ready for anova function
        samples = []
        for grouping_fld_val_spec in grouping_fld_vals_spec:
            grouping_filt = ValFilterSpec(variable_name=self.grouping_field_name, val_spec=grouping_fld_val_spec,
                val_is_numeric=grouping_val_is_numeric)
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                grouping_filt=grouping_filt, measure_fld_name=self.measure_field_name,
                tbl_filt_clause=self.table_filter)
            samples.append(sample)
        stats_result = anova_stats_calc(grouping_fld_lbl, measure_fld_lbl, samples, high=self.high_precision_required)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## labels
        grouping_fld_lbl = self.data_labels.var2var_lbl.get(self.grouping_field_name, self.grouping_field_name)
        measure_fld_lbl = self.data_labels.var2var_lbl.get(self.measure_field_name, self.measure_field_name)
        val2lbl = self.data_labels.var2val2lbl.get(self.grouping_field_name, {})
        grouping_fld_vals_spec = list({
            ValSpec(val=group_val, lbl=val2lbl.get(group_val, str(group_val))) for group_val in self.group_values})
        grouping_fld_vals_spec.sort(key=lambda vs: vs.lbl)
        ## data
        grouping_val_is_numeric = all(is_numeric(x) for x in self.group_values)
        ## build sample results ready for anova function
        samples = []
        for grouping_fld_val_spec in grouping_fld_vals_spec:
            grouping_filt = ValFilterSpec(variable_name=self.grouping_field_name, val_spec=grouping_fld_val_spec,
                val_is_numeric=grouping_val_is_numeric)
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                grouping_filt=grouping_filt, measure_fld_name=self.measure_field_name,
                tbl_filt_clause=self.table_filter)
            samples.append(sample)
        ## calculations
        stats_result = anova_stats_calc(grouping_fld_lbl, measure_fld_lbl, samples, high=self.high_precision_required)
        ## output
        histograms2show = []
        for group_spec in stats_result.group_specs:
            try:
                histogram_html = get_embedded_histogram_html(
                    measure_fld_lbl, style_spec.chart, group_spec.vals, group_spec.lbl)
            except Exception as e:
                html_or_msg = f"<b>{group_spec.lbl}</b> - unable to display histogram. Reason: {e}"
            else:
                html_or_msg = histogram_html
            histograms2show.append(html_or_msg)
        result = Result(**todict(stats_result),
            group_lbl=grouping_fld_lbl,
            measure_fld_lbl=measure_fld_lbl,
            histograms2show=histograms2show,
        )
        html = get_html(result, style_spec, dp=self.decimal_points)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
