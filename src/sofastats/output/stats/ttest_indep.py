from dataclasses import dataclass
from typing import Any, Sequence

import jinja2
import pandas as pd

from sofastats.data_extraction.interfaces import ValFilterSpec
from sofastats.data_extraction.utils import get_sample
from sofastats.output.charts import mpl_pngs
from sofastats.output.interfaces import DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType
from sofastats.output.stats.interfaces import CommonStatsDesign
from sofastats.output.stats.common import get_embedded_histogram_html
from sofastats.output.stats.msgs import (
    CI_EXPLAIN, KURTOSIS_EXPLAIN,
    NORMALITY_MEASURE_EXPLAIN, OBRIEN_EXPLAIN, P_EXPLAIN_TWO_GROUPS,
    SKEW_EXPLAIN, STD_DEV_EXPLAIN,
)
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats.stats_calc.engine import ttest_ind as ttest_indep_stats_calc
from sofastats.stats_calc.interfaces import NumericParametricSampleSpecFormatted, TTestIndepResult
from sofastats.stats_calc.utils import get_samples_from_df
from sofastats.utils.maths import format_num, is_numeric
from sofastats.utils.misc import todict
from sofastats.utils.stats import get_p_str

def independent_samples_t_test_from_df(df: pd.DataFrame) -> TTestIndepResult:
    """
    Does group A have a different average metric value from group B?

    Args:
        df: first col must have two values, one for each group, and the second col must have floats
    """
    samples = get_samples_from_df(df, n_expected_groups=2)
    sample_a, sample_b = samples
    stats_result = ttest_indep_stats_calc(sample_a=sample_a, sample_b=sample_b)
    return stats_result

@dataclass(frozen=True)
class Result(TTestIndepResult):
    grouping_field_name: str
    measure_field_name: str
    histograms2show: Sequence[str]
    decimal_points: int = 3

def get_html(result: Result, style_spec: StyleSpec) -> str:
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
            <td class='lbl-{{ style_name_hyphens }}'>{{group_spec.lbl}}</td>
            <td class='right'>{{ group_spec.n }}</td>
            <td class='right'>{{ group_spec.mean }}</td>
            <td class='right'>{{ group_spec.ci95 }}</td>
            <td class='right'>{{ group_spec.std_dev }}</td>
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
      {{histogram2show}}  <!-- either an <img> or an error message <p> -->
    {% endfor %}

    <p>No worked example available for this test</p>

    </div>
    """
    dp = result.decimal_points
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    title = (f'Results of independent samples t-test of average "{result.measure_field_name}" '
        f'''for "{result.grouping_field_name}" groups "{result.group_a_spec.label}" and "{result.group_b_spec.label}"''')
    num_tpl = f"{{:,.{dp}f}}"  ## use comma as thousands separator, and display specified decimal places
    ## format group details needed by second table
    formatted_group_specs = []
    for orig_group_spec in [result.group_a_spec, result.group_b_spec]:
        n = format_num(orig_group_spec.n)
        ci95_left = num_tpl.format(round(orig_group_spec.ci95[0], dp))
        ci95_right = num_tpl.format(round(orig_group_spec.ci95[1], dp))
        ci95 = f"{ci95_left} - {ci95_right}"
        std_dev = num_tpl.format(round(orig_group_spec.std_dev, dp))
        sample_mean = num_tpl.format(round(orig_group_spec.mean, dp))
        kurt = num_tpl.format(round(orig_group_spec.kurtosis, dp))
        skew_val = num_tpl.format(round(orig_group_spec.skew, dp))
        formatted_group_spec = NumericParametricSampleSpecFormatted(
            label=orig_group_spec.label,
            n=n,
            mean=sample_mean,
            ci95=ci95,
            std_dev=std_dev,
            sample_min=str(orig_group_spec.sample_min),
            sample_max=str(orig_group_spec.sample_max),
            kurtosis=kurt,
            skew=skew_val,
            p=str(result.p),
        )
        formatted_group_specs.append(formatted_group_spec)
    label_a = result.group_a_spec.label
    label_b = result.group_b_spec.label
    two_tailed_explanation = (
        "This is a two-tailed result i.e. based on the likelihood of a difference "
        f'where the direction ("{label_a}" higher than "{label_b}" or "{label_b}" higher than "{label_a}") '
        "doesn't matter.")
    p_full_explanation = f"{P_EXPLAIN_TWO_GROUPS}<br><br>{two_tailed_explanation}"

    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'style_name_hyphens': style_spec.style_name_hyphens,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'degrees_of_freedom': result.degrees_of_freedom,
        'footnotes': [p_full_explanation,
            OBRIEN_EXPLAIN, CI_EXPLAIN, STD_DEV_EXPLAIN, KURTOSIS_EXPLAIN, SKEW_EXPLAIN, NORMALITY_MEASURE_EXPLAIN],
        'group_specs': formatted_group_specs,
        'histograms2show': result.histograms2show,
        'obriens_msg': result.obriens_msg,
        'p': get_p_str(result.p),
        't': round(result.t, dp),
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@dataclass(frozen=False)
class TTestIndepDesign(CommonStatsDesign):
    """
    Args:
        measure_field_name: the name of the field aggregated by group - the analysis compares the mean value of each group.
            For example, 'Age'
        grouping_field_name: the name of the field used to define the groups compared in the analysis e.g. 'Country'
        group_a_value: the analysis will compare the mean value for this group
            against the mean value of the group defined by group_b_value
        group_b_value: the analysis will compare the mean value of this group
            against the mean value of the group defined by group_a_value
    """
    measure_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    grouping_field_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_a_value: Any = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    group_b_value: Any = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    def to_result(self) -> TTestIndepResult:
        ## data
        ## build samples ready for ttest_indep function
        grouping_filt_a = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_a_value, val_is_numeric=is_numeric(self.group_a_value))
        sample_a = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filt=grouping_filt_a, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        grouping_filt_b = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_b_value, val_is_numeric=is_numeric(self.group_b_value))
        sample_b = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filt=grouping_filt_b, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        ## get result
        stats_result = ttest_indep_stats_calc(sample_a, sample_b)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        ## build samples ready for ttest_indep function
        grouping_filt_a = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_a_value, val_is_numeric=is_numeric(self.group_a_value))
        sample_a = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filt=grouping_filt_a, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        grouping_filt_b = ValFilterSpec(variable_name=self.grouping_field_name,
            value=self.group_b_value, val_is_numeric=is_numeric(self.group_b_value))
        sample_b = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, source_table_name=self.source_table_name,
            grouping_filt=grouping_filt_b, measure_field_name=self.measure_field_name,
            table_filter_sql=self.table_filter_sql)
        ## get result
        stats_result = ttest_indep_stats_calc(sample_a, sample_b)

        mpl_pngs.set_gen_mpl_settings(axes_label_size=10, xtick_label_size=8, ytick_label_size=8)
        histograms2show = []
        for group_spec in [stats_result.group_a_spec, stats_result.group_b_spec]:
            try:
                histogram_html = get_embedded_histogram_html(
                    self.measure_field_name, style_spec.chart, group_spec.vals, group_spec.label)
            except Exception as e:
                html_or_msg = f"<b>{group_spec.label}</b> - unable to display histogram. Reason: {e}"
            else:
                html_or_msg = histogram_html
            histograms2show.append(html_or_msg)

        result = Result(**todict(stats_result),
            grouping_field_name=self.grouping_field_name,
            measure_field_name=self.measure_field_name,
            histograms2show=histograms2show,
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
