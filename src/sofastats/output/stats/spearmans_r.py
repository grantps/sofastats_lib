from dataclasses import dataclass
from functools import partial

import jinja2
import pandas as pd

from sofastats.data_extraction.utils import get_paired_data
from sofastats.output.stats.common import get_optimal_min_max
from sofastats.output.charts.mpl_pngs import get_scatterplot_fig
from sofastats.output.charts.scatter_plot import ScatterplotConf, ScatterplotSeries
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.output.stats.interfaces import Coord, CorrelationResult
from sofastats.output.stats.msgs import TWO_TAILED_EXPLANATION
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_style_spec
from sofastats.output.utils import get_p_explain, plot2image_as_data
from sofastats.stats_calc.engine import get_regression_result, spearmansr as spearmansr_stats_calc
from sofastats.stats_calc.interfaces import CorrelationCalcResult
from sofastats.stats_calc.spearmansr import get_worked_result
from sofastats.utils.maths import format_num
from sofastats.utils.misc import pluralise_with_s, todict
from sofastats.utils.stats import get_p_str

def spearmans_r_from_df(df: pd.DataFrame) -> CorrelationCalcResult:
    """
    Are variables A and B correlated?

    Args:
        df: first and second col must have floats
    """
    df.columns = ['a', 'b']
    a_vals = list(df['a'])
    b_vals = list(df['b'])
    stats_result = spearmansr_stats_calc(a_vals, b_vals)
    return stats_result

@dataclass(frozen=True)
class Result(CorrelationResult):
    scatterplot_html: str
    worked_example: str

def get_worked_example(result: CorrelationResult, style_name_hyphens: str) -> str:
    row_or_rows_str = partial(pluralise_with_s, singular_word='row')
    css_first_row_var = f"firstrowvar-{style_name_hyphens}"
    html = [(f"""<hr>
    <h2>Worked Example of Key Calculations</h2>
    <h3>Step 1 - Set up table of paired results</h3>
    <table>
    <thead>
      <tr>
          <th class='{css_first_row_var}'>{result.variable_a_name}</th>
          <th class='{css_first_row_var}'>{result.variable_b_name}</th>
      </tr>
    </thead>
    <tbody>""")]
    max_display_rows = 50
    init_tbl = result.worked_result.initial_tbl
    for row in init_tbl[:max_display_rows]:
        html.append(f"<tr><td>{row.x}</td><td>{row.y}</td></tr>")
    diff_init = len(init_tbl) - max_display_rows
    if diff_init > 0:
        html.append(f"<tr><td colspan='2'>{format_num(diff_init)} {row_or_rows_str(n_items=diff_init)} not displayed</td></tr>")
    html.append('</tbody></table>')
    html.append(f"""
      <h3>Step 2 - Work out ranks for the x and y values</h3>
      <p>Rank such that all examples of a value get the mean rank for all
      items of that value</p>
      <table>
      <thead>
          <tr>
          <th class='{css_first_row_var}'>{result.variable_a_name}</th>
          <th class='{css_first_row_var}'>Rank within<br>{result.variable_b_name}</th></tr>
      </thead>
      <tbody>""")
    x_ranked = result.worked_result.x_and_rank
    for x, x_rank in x_ranked[:max_display_rows]:
        html.append(f'<tr><td>{x}</td><td>{x_rank}</td></tr>')
    diff_x_ranked = len(x_ranked) - max_display_rows
    if diff_x_ranked > 0:
        html.append(
            f"<tr><td colspan='2'>{format_num(diff_x_ranked)} {row_or_rows_str(n_items=diff_x_ranked)} not displayed</td></tr>")
    html.append('</tbody></table>')
    html.append(f"""
      <p>Do the same for {result.variable_b_name} values</p>
      <table>
      <thead>
          <tr>
            <th class='{css_first_row_var}'>{result.variable_b_name}</th>
            <th class='{css_first_row_var}'>Rank within<br>{result.variable_b_name}</th>
          </tr>
      </thead>
      <tbody>""")
    y_ranked = result.worked_result.y_and_rank
    for y, y_rank in y_ranked[:max_display_rows]:
        html.append(f'<tr><td>{y}</td><td>{y_rank}</td></tr>')
    diff_y_ranked = len(y_ranked) - max_display_rows
    if diff_y_ranked > 0:
        html.append(
            f"<tr><td colspan='2'>{format_num(diff_y_ranked)} {row_or_rows_str(n_items=diff_y_ranked)} not displayed</td></tr>")
    html.append('</tbody></table>')
    html.append(f"""
      <h3>Step 3 - Add ranks to original table or pairs</h3>
      <table>
      <thead>
          <tr>
              <th class='{css_first_row_var}'>{result.variable_a_name}</th>
              <th class='{css_first_row_var}'>{result.variable_b_name}</th>
              <th class='{css_first_row_var}'>{result.variable_a_name} Ranks</th>
              <th class='{css_first_row_var}'>{result.variable_b_name} Ranks</th>
          </tr>
      </thead>
      <tbody>""")
    for row in init_tbl[:max_display_rows]:
        html.append(f"<tr><td>{row.x}</td><td>{row.y}</td><td>{row.rank_x}</td><td>{row.rank_y}</td></tr>")
    if diff_init > 0:
        html.append(f"<tr><td colspan='4'>{format_num(diff_init)} {row_or_rows_str(n_items=diff_init)} not displayed</td></tr>")
    html.append('</tbody></table>')
    html.append(f"""
      <h3>Step 4 - Add difference in ranks and get square of diff</h3>
      <table>
      <thead>
          <tr>
              <th class='{css_first_row_var}'>{result.variable_a_name}</th>
              <th class='{css_first_row_var}'>{result.variable_b_name}</th>
              <th class='{css_first_row_var}'>{result.variable_a_name} Ranks</th>
              <th class='{css_first_row_var}'>{result.variable_b_name} Ranks</th>
              <th class='{css_first_row_var}'>Difference</th>
              <th class='{css_first_row_var}'>Diff Squared</th>
          </tr>
      </thead>
      <tbody>""")
    for row in init_tbl[:max_display_rows]:
        html.append(f"""<tr>
              <td>{row.x}</td>
              <td>{row.y}</td>
              <td>{row.diff}</td>
              <td>{row.rank_x}</td>
              <td>{row.rank_y}</td>
              <td>{row.diff_squared}</td>
          </tr>""")
    if diff_init > 0:
        html.append(f"<tr><td colspan='6'>{format_num(diff_init)} {row_or_rows_str(n_items=diff_init)} not displayed</td></tr>")
    html.append('</tbody></table>')
    n = format_num(result.worked_result.n_x)
    n_cubed_minus_n = format_num(result.worked_result.n_cubed_minus_n)
    html.append(f"""
      <h3>Step 5 - Count N pairs, cube it, and subtract N</h3>
      N = {n}<br>N<sup>3</sup> - N = {n_cubed_minus_n}""")
    tot_d_squared = format_num(result.worked_result.tot_d_squared)
    tot_d_squared_minus_6 = format_num(result.worked_result.tot_d_squared_x_6)
    n_cubed_minus_n = format_num(result.worked_result.n_cubed_minus_n)
    pre_rho = format_num(result.worked_result.pre_rho)
    rho = result.worked_result.rho
    html.append(f"""
      <h3>Step 6 - Total squared diffs, multiply by 6, divide by N<sup>3</sup> -
      N value</h3>
      Total squared diffs = {tot_d_squared}
      <br>Multiplied by 6 = {tot_d_squared_minus_6}<br>
      Divided by N<sup>3</sup> - N value ({n_cubed_minus_n}) = {pre_rho}
      """)
    html.append(f"""
      <h3>Step 7 - Subtract from 1 to get Spearman's rho</h3>
      rho = 1 - {pre_rho} = {rho} (all rounded to 4dp)""")
    html.append(
        "<p>The only remaining question is the probability of a rho that size occurring for a given N value</p>")
    return '\n'.join(html)

def get_html(result: Result, style_spec: StyleSpec, *, dp: int, show_workings=False) -> str:
    tpl = """\
    <h2>{{ title }}</h2>

    <p>Two-tailed p value: {{ p_str }} <a href='#ft1'><sup>1</sup></a></p>

    <p>Spearman's R statistic: {{ spearmans_r_rounded }}</p>

    <p>{{ degrees_of_freedom_msg }}</p>

    <p>Linear Regression Details: <a href='#ft2'><sup>2</sup></a></p>

    <ul>
        <li>Slope: {{ slope_rounded }}</li>
        <li>Intercept: {{ intercept_rounded }}</li>
    </ul>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup>{{ loop.index }}</sup>{{ footnote }}</p>
    {% endfor %}

    {{ scatterplot_html }}

    {% if worked_example %}
      {{ worked_example }}
    {% endif %}
    """
    title = ('''Results of Spearman's Test of Linear Correlation for '''
        f'''"{result.variable_a_name}" vs "{result.variable_b_name}"''')
    p_str = get_p_str(result.stats_result.p)
    p_explain = get_p_explain(result.variable_a_name, result.variable_b_name)
    p_full_explanation = f"{p_explain}</br></br>{TWO_TAILED_EXPLANATION}"
    spearmans_r_rounded = round(result.stats_result.r, dp)
    degrees_of_freedom_msg = f"Degrees of Freedom (df): {result.stats_result.degrees_of_freedom}"
    look_at_scatterplot_msg = "Always look at the scatter plot when interpreting the linear regression line."
    slope_rounded = round(result.regression_result.slope, dp)
    intercept_rounded = round(result.regression_result.intercept, dp)


    context = {
        'degrees_of_freedom_msg': degrees_of_freedom_msg,
        'footnotes': [p_full_explanation, look_at_scatterplot_msg],
        'intercept_rounded': intercept_rounded,
        'p_str': p_str,
        'spearmans_r_rounded': spearmans_r_rounded,
        'scatterplot_html': result.scatterplot_html,
        'slope_rounded': slope_rounded,
        'title': title,
        'worked_example': result.worked_example,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@dataclass(frozen=False)
class SpearmansRDesign(CommonDesign):
    variable_a_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    variable_b_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    style_name: str = 'default'
    decimal_points: int = 3
    show_workings: bool = False
    high_volume_ok: bool = False

    def to_result(self) -> CorrelationCalcResult:
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            tbl_filt_clause=self.table_filter)
        stats_result = spearmansr_stats_calc(paired_data.sample_a.vals, paired_data.sample_b.vals)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        paired_data = get_paired_data(cur=self.cur, dbe_spec=self.dbe_spec, src_tbl_name=self.source_table_name,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            tbl_filt_clause=self.table_filter)
        coords = [Coord(x=x, y=y) for x, y in zip(paired_data.sample_a.vals, paired_data.sample_b.vals, strict=True)]
        pearsonsr_calc_result = spearmansr_stats_calc(paired_data.sample_a.vals, paired_data.sample_b.vals,
            high_volume_ok=self.high_volume_ok)
        regression_result = get_regression_result(xs=paired_data.sample_a.vals,ys=paired_data.sample_b.vals)

        if self.show_workings:
            worked_result = get_worked_result(
                variable_a_values=paired_data.sample_a.vals,
                variable_b_values=paired_data.sample_b.vals,
            )
        else:
            worked_result = None

        correlation_result = CorrelationResult(
            variable_a_name=self.variable_a_name,
            variable_b_name=self.variable_b_name,
            coords=coords,
            stats_result=pearsonsr_calc_result,
            regression_result=regression_result,
            worked_result=worked_result,
        )

        worked_example = (
            get_worked_example(correlation_result, style_spec.style_name_hyphens) if self.show_workings else '')

        scatterplot_series = ScatterplotSeries(
            coords=coords,
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
            x_axis_label=self.variable_a_name,
            y_axis_label=self.variable_b_name,
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
            worked_example=worked_example,
        )
        html = get_html(result, style_spec, dp=self.decimal_points, show_workings=self.show_workings)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )
