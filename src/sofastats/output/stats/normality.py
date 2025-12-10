from dataclasses import dataclass

import jinja2
import pandas as pd

from sofastats import logger
from sofastats.conf.main import MIN_VALS_FOR_NORMALITY_TEST, N_WHERE_NORMALITY_USUALLY_FAILS_NO_MATTER_WHAT
from sofastats.data_extraction.utils import get_paired_diffs_sample, get_sample
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign, add_common_methods_from_parent)
from sofastats.output.stats.common import get_embedded_histogram_html
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec
from sofastats.stats_calc.engine import normal_test
from sofastats.stats_calc.interfaces import NormalTestResult

def normality_from_df(df: pd.DataFrame) -> NormalTestResult:
    """
    How normal is the distribution supplied?

    Args:
        df: first and only col must have floats
    """
    stats_result = normal_test(df.iloc[:, 0])
    return stats_result

@dataclass(frozen=True)
class Result:
    title: str
    message: str
    histogram: str

def get_html(result: Result) -> str:
    tpl = """\
    <style>
        {{ generic_unstyled_css }}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>

    {{ histogram }}

    {{ message }}

    </div>
    """
    generic_unstyled_css = get_generic_unstyled_css()

    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'histogram': result.histogram,
        'message': result.message,
        'title': result.title,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@add_common_methods_from_parent
@dataclass(frozen=False)
class NormalityDesign(CommonDesign):
    variable_a_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    variable_b_name: str | None = None

    style_name: str = 'default'

    decimal_points: int = 3

    def to_result(self) -> NormalTestResult:
        ## labels
        variable_a_label = self.data_labels.var2var_lbl.get(self.variable_a_name, self.variable_a_name)
        paired = self.variable_b_name is not None
        ## data
        if paired:
            variable_b_label = self.data_labels.var2var_lbl.get(self.variable_b_name, self.variable_b_name)
            sample = get_paired_diffs_sample(
                cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                variable_a_name=self.variable_a_name, variable_a_label=variable_a_label,
                variable_b_name=self.variable_b_name, variable_b_label=variable_b_label,
                tbl_filt_clause=self.table_filter)
        else:
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                measure_fld_name=self.variable_a_name, grouping_filt=None, tbl_filt_clause=self.table_filter)
        n_vals = len(sample.vals)
        if n_vals < MIN_VALS_FOR_NORMALITY_TEST:
            raise Exception(f"We need at least {MIN_VALS_FOR_NORMALITY_TEST:,} values to test normality.")
        else:
            stats_result = normal_test(sample.vals)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## labels
        variable_a_label = self.data_labels.var2var_lbl.get(self.variable_a_name, self.variable_a_name)
        paired = self.variable_b_name is not None
        ## data
        if paired:
            variable_b_label = self.data_labels.var2var_lbl.get(self.variable_b_name, self.variable_b_name)
            data_label = f'Difference Between "{variable_a_label}" and "{variable_b_label}"'
            sample = get_paired_diffs_sample(
                cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                variable_a_name=self.variable_a_name, variable_a_label=variable_a_label,
                variable_b_name=self.variable_b_name, variable_b_label=variable_b_label,
                tbl_filt_clause=self.table_filter)
        else:
            data_label = variable_a_label
            sample = get_sample(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
                measure_fld_name=self.variable_a_name, grouping_filt=None, tbl_filt_clause=self.table_filter)
        title = f"Normality Tests for {data_label}"
        ## message
        n_vals = len(sample.vals)
        if n_vals < MIN_VALS_FOR_NORMALITY_TEST:
            message = (f"<p>We need at least {MIN_VALS_FOR_NORMALITY_TEST:,} values to test normality.</p>"
            "<p>Rely entirely on visual inspection of graph above.</p>")
        else:
            try:
                stats_result = normal_test(sample.vals)
            except Exception as e:
                logger.info(f"Unable to calculate normality. Orig error: {e}")
                message = "<p>Unable to calculate normality tests</p>"
            else:
                ## skew
                if abs(stats_result.c_skew) <= 1:
                    skew_indication = 'a great sign'
                elif abs(stats_result.c_skew) <= 2:
                    skew_indication = 'a good sign'
                else:
                    skew_indication = 'not a good sign'
                skew_msg = (f"Skew (lopsidedness) is {round(stats_result.c_skew, self.decimal_points)} "
                    f"which is probably {skew_indication}.")
                ## kurtosis
                if abs(stats_result.c_kurtosis) <= 1:
                    kurtosis_indication = 'a great sign'
                elif abs(stats_result.c_kurtosis) <= 2:
                    kurtosis_indication = 'a good sign'
                else:
                    kurtosis_indication = 'not a good sign'
                kurtosis_msg = (
                    f"Kurtosis (peakedness or flatness) is {round(stats_result.c_kurtosis, self.decimal_points)} "
                    f"which is probably {kurtosis_indication}.")
                ## combined
                if n_vals > N_WHERE_NORMALITY_USUALLY_FAILS_NO_MATTER_WHAT:
                    message = ("<p>Rely on visual inspection of graph to assess normality.</p>"
                        "<p>Although the data failed the ideal normality test, "
                        f"most real-world data-sets with as many results ({n_vals:,}) would fail "
                        f"for even slight differences from the perfect normal curve.</p>"
                        f"<p>{skew_msg}</p><p>{kurtosis_msg}</p>")
                else:
                    if stats_result.p < 0.05:
                        message = (f"<p>The distribution of {data_label} passed one test for normality.</p>"
                            f"<p>Confirm or reject based on visual inspection of graph. {skew_msg} {kurtosis_msg}</p>")
                    else:
                        message = (f'<p>Although the distribution of {data_label} is not perfectly "normal", '
                            f'it may still be "normal" enough for use. View graph to decide.</p>'
                            f"<p>{skew_msg}</p></p>{kurtosis_msg}</p>")
        ## histogram
        histogram = get_embedded_histogram_html(measure_fld_lbl=data_label, style_spec=style_spec.chart,
            vals=sample.vals, width_scalar=1.5, label_chart_from_var_if_needed=False)

        result = Result(
            title=title,
            message=message,
            histogram=histogram,
        )
        html = get_html(result)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
