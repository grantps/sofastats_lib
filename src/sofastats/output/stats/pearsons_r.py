from dataclasses import dataclass

import jinja2
import pandas as pd

from sofastats.data_extraction.utils import get_paired_data
from sofastats.output.stats.common import get_optimal_min_max
from sofastats.output.charts.mpl_pngs import get_scatterplot_fig
from sofastats.output.charts.scatterplot import ScatterplotConf, ScatterplotSeries
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign, add_common_methods_from_parent)
from sofastats.output.stats.interfaces import Coord, CorrelationResult
from sofastats.output.stats.msgs import ONE_TAILED_EXPLANATION
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_style_spec
from sofastats.output.utils import get_p_explain, plot2image_as_data
from sofastats.stats_calc.engine import get_regression_result, pearsonr as pearsonsr_stats_calc
from sofastats.stats_calc.interfaces import CorrelationCalcResult
from sofastats.utils.misc import todict
from sofastats.utils.stats import get_p_str

def pearsons_r_from_df(df: pd.DataFrame) -> CorrelationCalcResult:
    """
    Are variables A and B correlated?

    Args:
        df: first and second col must have floats
    """
    df.columns = ['a', 'b']
    a_vals = list(df['a'])
    b_vals = list(df['b'])
    stats_result = pearsonsr_stats_calc(a_vals, b_vals)
    return stats_result

@dataclass(frozen=True)
class Result(CorrelationResult):
    scatterplot_html: str

def get_html(result: Result, style_spec: StyleSpec, *, dp: int) -> str:
    tpl = """\
    <h2>{{ title }}</h2>

    <p>Two-tailed p value: {{ p_str }} <a href='#ft1'><sup>1</sup></a></p>

    <p>Pearson's R statistic: {{ pearsons_r_rounded }}</p>

    <p>{{ degrees_of_freedom_msg }}</p>

    <p>Linear Regression Details: <a href='#ft2'><sup>2</sup></a></p>

    <ul>
        <li>Slope: {{ slope_rounded }}</li>
        <li>Intercept: {{ intercept_rounded }}</li>
    </ul>

    {{ scatterplot_html }}

    <p>No worked example available for this test</p>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup>{{ loop.index }}</sup>{{ footnote }}</p>
    {% endfor %}
    """
    title = ('''Results of Pearson's Test of Linear Correlation for '''
        f'''"{result.variable_a_name}" vs "{result.variable_b_name}"''')
    p_str = get_p_str(result.stats_result.p)
    p_explain = get_p_explain(result.variable_a_name, result.variable_b_name)
    p_full_explanation = f"{p_explain}</br></br>{ONE_TAILED_EXPLANATION}"
    pearsons_r_rounded = round(result.stats_result.r, dp)
    degrees_of_freedom_msg = f"Degrees of Freedom (df): {result.stats_result.degrees_of_freedom}"
    look_at_scatterplot_msg = "Always look at the scatter plot when interpreting the linear regression line."
    slope_rounded = round(result.regression_result.slope, dp)
    intercept_rounded = round(result.regression_result.intercept, dp)

    context = {
        'degrees_of_freedom_msg': degrees_of_freedom_msg,
        'footnotes': [p_full_explanation, look_at_scatterplot_msg],
        'intercept_rounded': intercept_rounded,
        'p_str': p_str,
        'pearsons_r_rounded': pearsons_r_rounded,
        'scatterplot_html': result.scatterplot_html,
        'slope_rounded': slope_rounded,
        'title': title,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@add_common_methods_from_parent
@dataclass(frozen=False)
class PearsonsRDesign(CommonDesign):
    variable_a_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    variable_b_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    style_name: str = 'default'
    decimal_points: int = 3

    def to_result(self) -> CorrelationCalcResult:
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            tbl_filt_clause=self.table_filter)
        stats_result = pearsonsr_stats_calc(paired_data.sample_a.vals, paired_data.sample_b.vals)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            tbl_filt_clause=self.table_filter)
        coords = [Coord(x=x, y=y) for x, y in zip(paired_data.sample_a.vals, paired_data.sample_b.vals, strict=True)]
        pearsonsr_calc_result = pearsonsr_stats_calc(paired_data.sample_a.vals, paired_data.sample_b.vals)
        regression_result = get_regression_result(xs=paired_data.sample_a.vals,ys=paired_data.sample_b.vals)

        correlation_result = CorrelationResult(
            variable_a_name=self.variable_a_name,
            variable_b_name=self.variable_b_name,
            coords=coords,
            stats_result=pearsonsr_calc_result,
            regression_result=regression_result,
        )

        scatterplot_series = ScatterplotSeries(
            coords=correlation_result.coords,
            dot_colour=style_spec.chart.colour_mappings[0].main,
            dot_line_colour=style_spec.chart.major_grid_line_colour,
            show_regression_details=True,
        )
        vars_series = [scatterplot_series, ]
        xs = correlation_result.xs
        ys = correlation_result.ys
        x_min, x_max = get_optimal_min_max(axis_min=min(xs), axis_max=max(xs))
        y_min, y_max = get_optimal_min_max(axis_min=min(ys), axis_max=max(ys))
        chart_conf = ScatterplotConf(
            width_inches=7.5,
            height_inches=4.0,
            inner_background_colour=style_spec.chart.plot_bg_colour,
            text_colour=style_spec.chart.axis_font_colour,
            x_axis_label=correlation_result.variable_a_name,
            y_axis_label=correlation_result.variable_b_name,
            show_dot_lines=True,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )
        fig = get_scatterplot_fig(vars_series, chart_conf)
        image_as_data = plot2image_as_data(fig)
        scatterplot_html = f'<img src="{image_as_data}"/>'

        result = Result(**todict(correlation_result),
            scatterplot_html=scatterplot_html,
        )
        html = get_html(result, style_spec, dp=self.decimal_points)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
