from collections.abc import Collection, Sequence
from dataclasses import dataclass
from html import escape as html_escape
from itertools import product
from typing import Any

import jinja2
import numpy as np
import pandas as pd

from sofastats import logger
from sofastats.data_extraction.stats.chi_square import get_chi_square_data
from sofastats.output.charts import boomslang
from sofastats.output.interfaces import (
    DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY, HTMLItemSpec, OutputItemType, CommonDesign)
from sofastats.stats_calc.chi_square import WorkedResult, get_worked_result
from sofastats.output.styles.interfaces import StyleSpec
from sofastats.output.styles.utils import get_generic_unstyled_css, get_style_spec, get_styled_stats_tbl_css
from sofastats.output.utils import format_num, get_p, get_p_explain
from sofastats.stats_calc.engine import chisquare as chi_square_stats_calc
from sofastats.stats_calc.interfaces import ChiSquareResult
from sofastats.output.utils import plot2image_as_data

def chi_square_from_df(df: pd.DataFrame) -> ChiSquareResult:
    """
    Args:
        df: must have two columns - one for each group.

    See data_extraction.stats.chi_square.get_chi_square_data (similar logic with SQL base)
    """
    total_observed_values = len(df)
    if total_observed_values < 50:
        raise Exception("Probably not enough values to run Chi Square Test")
    df.columns = ['a', 'b']
    df_grouped = df.groupby(['a', 'b']).size().reset_index(name='freq')
    observed_values_a_then_b_ordered = list(df_grouped['freq'])
    df_a_grouped = df.groupby('a').size().reset_index(name='freq')
    df_b_grouped = df.groupby('b').size().reset_index(name='freq')
    fractions_of_total_for_variable_a = df_a_grouped['freq'] / total_observed_values
    fractions_of_total_for_variable_b = df_b_grouped['freq'] / total_observed_values
    expected_values_a_then_b_ordered = []
    for fraction_of_val_in_variable_a, fraction_of_val_in_variable_b in product(
            fractions_of_total_for_variable_a, fractions_of_total_for_variable_b):
        expected_values_a_then_b_ordered.append(fraction_of_val_in_variable_a * fraction_of_val_in_variable_b * total_observed_values)
    n_variable_a_vals = len(df_a_grouped)
    n_variable_b_vals = len(df_b_grouped)
    degrees_of_freedom = (n_variable_a_vals - 1) * (n_variable_b_vals - 1)
    stats_result = chi_square_stats_calc(
        f_obs=observed_values_a_then_b_ordered,
        f_exp=expected_values_a_then_b_ordered,
        df=degrees_of_freedom)
    return stats_result

@dataclass(frozen=True)
class Result:
    variable_a_name: str
    variable_b_name: str
    variable_a_values: Sequence[str | int]
    variable_b_values: Sequence[str | int]
    observed_values_a_then_b_ordered: Sequence[float]
    expected_values_a_then_b_ordered: Sequence[float]
    p: float
    chi_square: float
    degrees_of_freedom: int
    minimum_cell_count: int
    pct_cells_lt_5: float
    observed_vs_expected_tbl: str
    chi_square_charts: str
    worked_example: str
    decimal_points: int = 3

def get_observed_vs_expected_tbl(
        variable_a_name: str, variable_b_name: str,
        variable_a_values: Sequence[str], variable_b_values: Sequence[str],
        observed_values_a_then_b_ordered: Sequence[float],
        expected_values_a_then_b_ordered: Sequence[float],
        style_name_hyphens: str) -> str:

    ## output.styles.utils.get_styled_stats_tbl_css controls the styles that will apply to these classes
    css_datacell = f"datacell-{style_name_hyphens}"
    css_spaceholder = f"spaceholder-{style_name_hyphens}"
    css_first_col_var = f"firstcolvar-{style_name_hyphens}"
    css_first_row_var = f"firstrowvar-{style_name_hyphens}"
    css_row_val = f"rowval-{style_name_hyphens}"
    cells_per_col = 2  ## obs, exp

    variable_a_label_html = html_escape(variable_a_name)
    variable_b_label_html = html_escape(variable_b_name)
    try:
        variable_a_values_html = list(map(html_escape, variable_a_values))
        variable_b_values_html = list(map(html_escape, variable_b_values))
    except AttributeError:
        ## e.g. an int
        variable_a_values_html = variable_a_values
        variable_b_values_html = variable_b_values

    n_variable_a_values = len(variable_a_values)
    n_variable_b_values = len(variable_b_values)

    html = []
    html.append(f"\n\n<table cellspacing='0'>\n<thead>")
    html.append(f"\n<tr><th class='{css_spaceholder}' colspan=2 rowspan=3></th>")
    colspan2use = (n_variable_b_values + 1) * cells_per_col
    html.append(f"<th class='{css_first_col_var}' colspan={colspan2use}>{variable_b_label_html}</th></tr>")
    html.append('\n<tr>')
    for val in variable_b_values_html:
        html.append(f'<th colspan={cells_per_col}>{val}</th>')
    html.append(f"<th colspan={cells_per_col}>TOTAL</th></tr>\n<tr>")
    for _val in range(n_variable_b_values + 1):
        html.append("<th>Obs</th><th>Exp</th>")
    html.append("</tr>")
    ## body
    html.append("\n\n</thead><tbody>")
    item_i = 0
    html.append(f"\n<tr><td class='{css_first_row_var}' rowspan={n_variable_a_values + 1}>{variable_a_label_html}</td>")
    col_obs_tots = [0, ] * n_variable_b_values
    col_exp_tots = [0, ] * n_variable_b_values
    ## total row totals
    row_obs_tot_tot = 0
    row_exp_tot_tot = 0
    for val_a in variable_a_values_html:
        row_obs_tot = 0
        row_exp_tot = 0
        html.append(f"<td class='{css_row_val}'>{val_a}</td>")
        for col_i, unused in enumerate(variable_b_values_html):
            obs = observed_values_a_then_b_ordered[item_i]
            exp = expected_values_a_then_b_ordered[item_i]
            html.append(f"<td class='{css_datacell}'>{obs}</td><td class='{css_datacell}'>{round(exp, 1)}</td>")
            row_obs_tot += obs
            row_exp_tot += exp
            col_obs_tots[col_i] += obs
            col_exp_tots[col_i] += exp
            item_i += 1
        ## add total for row
        row_obs_tot_tot += row_obs_tot
        row_exp_tot_tot += row_exp_tot
        html.append(f"<td class='{css_datacell}'>"
            + f"{row_obs_tot}</td><td class='{css_datacell}'>"
            + f'{round(row_exp_tot, 1)}</td>')
        html.append('</tr>\n<tr>')
    ## add totals row
    col_tots = zip(col_obs_tots, col_exp_tots)
    html.append(f"<td class='{css_row_val}'>TOTAL</td>")
    for col_obs_tot, col_exp_tot in col_tots:
        html.append(f"<td class='{css_datacell}'>{col_obs_tot}</td>"
            f"<td class='{css_datacell}'>{round(col_exp_tot, 1)}</td>")
    ## add total of totals
    tot_tot_str = round(row_exp_tot_tot, 1)
    html.append(f"<td class='{css_datacell}'>{row_obs_tot_tot}</td><td class='{css_datacell}'>{tot_tot_str}</td>")
    html.append('</tr>')
    html.append(f'\n</tbody>\n</table>\n')
    return '\n'.join(html)

def get_worked_example(worked_result: WorkedResult) -> str:
    html = []
    html.append("""
    <hr>
    <h2>Worked Example of Key Calculations</h2>
    <h3>Step 1 - Calculate row and column sums</h3>""")
    html.append('<h4>Row sums</h4>')
    for row_n in range(1, worked_result.row_n + 1):
        vals_added = ' + '.join(format_num(x) for x in worked_result.row_n2obs_row[row_n])
        row_sums = format_num(worked_result.row_n2row_sum[row_n])
        html.append(f"""
        <p>Row {row_n} Total: {vals_added} = <strong>{row_sums}</strong></p>
        """)
    html.append('<h4>Column sums</h4>')
    for col_n in range(1, worked_result.col_n + 1):
        vals_added = ' + '.join(format_num(x) for x in worked_result.col_n2obs_row[col_n])
        col_sums = format_num(worked_result.col_n2col_sum[col_n])
        html.append(f"""
        <p>Col {col_n} Total: {vals_added} = <strong>{col_sums}</strong></p>
        """)
    html.append("""
    <h3>Step 2 - Calculate expected values per cell</h3>
    <p>Multiply row and column sums for cell and divide by grand total
    </p>""")
    for coord, cell_data in worked_result.cells_data.items():
        row_n, col_n = coord
        row_sum = format_num(cell_data.row_sum)
        col_sum = format_num(cell_data.col_sum)
        grand_tot = format_num(worked_result.grand_tot)
        expected = format_num(cell_data.expected_value)
        html.append(f"""<p>Row {row_n}, Col {col_n}: ({row_sum} x {col_sum})
        /{grand_tot} = <strong>{expected}</strong></p>""")
    html.append("""
    <h3>Step 3 - Calculate the differences between observed and expected per
    cell, square them, and divide by expected value</h3>""")
    for coord, cell_data in worked_result.cells_data.items():
        row_n, col_n = coord
        larger = format_num(cell_data.max_of_observed_and_expected)
        smaller = format_num(cell_data.min_of_observed_and_expected)
        expected = format_num(cell_data.expected_value)
        diff = format_num(cell_data.expected_value)
        diff_squ = format_num(cell_data.diff_squared)
        pre_chi = format_num(cell_data.pre_chi)
        html.append(f"""
        <p>Row {row_n}, Col {col_n}:
        ({larger} - {smaller})<sup>2</sup> / {expected}
        = ({diff})<sup>2</sup> / {expected}
        = {diff_squ} / {expected}
        = <strong>{pre_chi}</strong></p>""")
    html.append(
        '<h3>Step 4 - Add up all the results to get Χ<sup>2</sup></h3>')
    vals_added = ' + '.join(str(x) for x in worked_result.pre_chis)
    html.append(
        f'<p>{vals_added} = <strong>{worked_result.chi_square}</strong></p>')
    row_n = worked_result.row_n
    col_n = worked_result.col_n
    row_n_minus_1 = worked_result.row_n_minus_1
    col_n_minus_1 = worked_result.col_n_minus_1
    degrees_of_freedom = worked_result.degrees_of_freedom
    html.append(f"""
    <h3>Step 5 - Calculate degrees of freedom</h3>
    <p>N rows - 1 multiplied by N columns - 1</p>
    <p>({row_n} - 1) x ({col_n} - 1) = {row_n_minus_1} x {col_n_minus_1}
    = <strong>{degrees_of_freedom}</strong></p>""")
    html.append("""<p>The only remaining question is the probability of a
        Chi Square value that size occurring for a given degrees of freedom
        value</p>""")
    return '\n'.join(html)

def get_x_axis_font_size(val_labels: Collection[str]) -> int:
    max_len = max(len(x) for x in val_labels)
    if max_len > 15:
        font_size = 7
    elif max_len > 10:
        font_size = 9
    elif max_len > 7:
        font_size = 10
    else:
        font_size = 11
    return font_size

def get_labels_in_lines(orig_txt: str, max_width: int, *, dojo=False, rotate=False) -> tuple[str, int, int]:
    """
    Returns quoted text. Will not be further quoted.
    Will be "%s" % wrapped txt not "\"%s\"" % wrapped_txt
    actual_label_width -- may be broken into lines if not rotated.
    If rotated, we need sum of each line (no line breaks possible at present).
    """
    lines = []
    try:
        words = orig_txt.split()
    except Exception:
        raise Exception("Tried to split a non-text label. Is the script not supplying text labels?")
    line_words = []
    for word in words:
        line_words.append(word)
        line_width = len(' '.join(line_words))
        if line_width > max_width:
            line_words.pop()
            lines.append(' '.join(line_words))
            line_words = [word]
    lines.append(' '.join(line_words))
    lines = [x.center(max_width) for x in lines]
    logger.debug(line_words)
    logger.debug(lines)
    n_lines = len(lines)
    if dojo:
        if n_lines == 1:
            raw_label = lines[0].strip()
            wrapped_txt = '"' + raw_label + '"'
            actual_label_width = len(raw_label)
        else:
            if rotate:  ## displays <br> for some reason so can't use it
                ## no current way identified for line breaks when rotated
                ## see - http://grokbase.com/t/dojo/dojo-interest/09cat4bkvg/dojox-charting-line-break-in-axis-labels-ie
                wrapped_txt = '"' + '" + " " + "'.join(x.strip() for x in lines) + '"'
                actual_label_width = sum(len(x)+1 for x in lines) - 1
            else:
                wrapped_txt = '"' + '" + labelLineBreak + "'.join(lines) + '"'
                actual_label_width = max_width  ## they are centred in max_width
    else:
        if n_lines == 1:
            raw_label = lines[0].strip()
            wrapped_txt = raw_label
            actual_label_width = len(raw_label)
        else:
            wrapped_txt = '\n'.join(lines)
            actual_label_width = max_width  ## they are centred in max_width
    logger.debug(wrapped_txt)
    return wrapped_txt, actual_label_width, n_lines

def config_clustered_barchart(plot, style_spec: StyleSpec, *,
        variable_a_label: str, variable_a_val_labels: Sequence[str], variable_b_val_labels: Sequence[str], y_label,
        as_in_bs_list: list[list[float]]):
    """
    Clustered bar charts

    Var A defines the clusters and B the split within the clusters e.g. gender
    vs country = gender as boomslang bars and country as values within bars.
    """
    grid_bg = style_spec.chart.chart_bg_colour
    bar_colours = [colour_with_highlight.main for colour_with_highlight in style_spec.chart.colour_mappings]
    clustered_bars = boomslang.ClusteredBars()
    clustered_bars.grid_bg = grid_bg
    labels_n = len(variable_b_val_labels)
    for i, val_label_b in enumerate(variable_b_val_labels):
        cluster = boomslang.Bar()
        x_vals = range(len(variable_a_val_labels))
        cluster.xValues = x_vals
        y_vals = as_in_bs_list[i]
        logger.debug(f'x_vals={x_vals}')
        logger.debug(f'y_vals={y_vals}')
        cluster.yValues = y_vals
        logger.debug(f"i={i}, bar_colours={bar_colours}")
        cluster.color = bar_colours[i]
        cluster.edgeColor = 'white'
        max_width = 17 if labels_n < 5 else 10
        cluster.label, _actual_label_width, _n_lines = get_labels_in_lines(orig_txt=val_label_b, max_width=max_width)
        clustered_bars.add(cluster)
    clustered_bars.spacing = 0.5
    clustered_bars.xTickLabels = variable_a_val_labels
    logger.debug(f'xTickLabels: {clustered_bars.xTickLabels}')
    plot.add(clustered_bars)
    plot.setXLabel(variable_a_label)
    plot.setYLabel(y_label)

def get_chi_square_charts(style_spec: StyleSpec,
        variable_a_name: str, variable_b_name: str,
        variable_a_values: Sequence[Any], variable_b_values: Sequence[Any],
        observed_values_a_then_b_ordered: Sequence[float],) -> str:
    """
    Delivered as base64-encoded binary images
    """
    html_bits = []
    ## NB observed_values_a_then_b_ordered is 'b's within 'a', and we need data structured the other way around
    n_clusters = variable_b_values_n = len(variable_b_values)
    if n_clusters < 8:
        width = 10
        height = None  ## allow height to be set by golden ratio
    else:
        width = n_clusters * 1.75
        height = 4.5
    rows_n = int(len(observed_values_a_then_b_ordered) / variable_b_values_n)
    cols_n = variable_b_values_n
    bs_in_as = np.array(observed_values_a_then_b_ordered).reshape(rows_n, cols_n)
    as_in_bs_list = bs_in_as.transpose().tolist()
    ## proportions of b within a
    proportions_of_bs_in_as = []
    ## expected proportion of b's in a's - so we have a reference to compare rest to
    total = sum(observed_values_a_then_b_ordered)
    expected_proportion_of_bs_in_as = []
    for as_in_b_list in as_in_bs_list:
        expected_proportion_of_bs_in_as.append(float(sum(as_in_b_list)) / float(total))
    proportions_of_bs_in_as.append(expected_proportion_of_bs_in_as)
    ## actual observed b's in a's
    bs_in_as_list = bs_in_as.tolist()
    for bs in bs_in_as_list:
        proportions_list = []
        for b in bs:
            proportions_list.append(float(b) / float(sum(bs)))
        proportions_of_bs_in_as.append(proportions_list)
    proportions_of_as_in_bs_list = np.array(proportions_of_bs_in_as).transpose().tolist()
    logger.debug(observed_values_a_then_b_ordered)
    logger.debug(bs_in_as)
    logger.debug(as_in_bs_list)
    logger.debug(bs_in_as_list)
    title_overrides = {'fontsize': 14}
    ## chart 1 - proportions ****************************************************
    plot_1 = boomslang.Plot()
    chart_1_title = f"{variable_a_name} and {variable_b_name} - Proportions"
    plot_1.setTitle(chart_1_title)
    plot_1.setTitleProperties(title_overrides)
    plot_1.setDimensions(width, height)
    plot_1.hasLegend(columns=variable_b_values_n, location='lower left')
    plot_1.setAxesLabelSize(11)
    plot_1.setXTickLabelSize(get_x_axis_font_size(variable_a_values))
    plot_1.setLegendLabelSize(9)
    variable_a_val_labels_with_ref = variable_a_values[:]
    variable_a_val_labels_with_ref.insert(0, "All\ncombined")
    config_clustered_barchart(plot_1, style_spec, variable_a_label=variable_a_name,
        variable_a_val_labels=variable_a_val_labels_with_ref, variable_b_val_labels=variable_b_values, y_label='Proportions',
        as_in_bs_list=proportions_of_as_in_bs_list)
    image_as_data_1 = plot2image_as_data(plot_1)
    html_bits.append(f'<img src="{image_as_data_1}"/>')
    ## chart 2 - freqs **********************************************************
    plot_2 = boomslang.Plot()
    chart_2_title = f"{variable_a_name} and {variable_b_name} - Frequencies"
    plot_2.setTitle(chart_2_title)
    plot_2.setTitleProperties(title_overrides)
    plot_2.setDimensions(width, height)
    plot_2.hasLegend(columns=len(variable_b_values), location='lower left')
    plot_2.setAxesLabelSize(11)
    plot_2.setXTickLabelSize(get_x_axis_font_size(variable_a_values))
    plot_2.setLegendLabelSize(9)
    ## only need 6 because program limits to that. See core_stats.get_obs_exp().  ## TODO - clarify 6 what etc
    config_clustered_barchart(plot_2, style_spec, variable_a_label=variable_a_name,
        variable_a_val_labels=variable_a_values, variable_b_val_labels=variable_b_values, y_label='Frequencies',
        as_in_bs_list=as_in_bs_list)
    image_as_data_2 = plot2image_as_data(plot_2)
    html_bits.append(f'<img src="{image_as_data_2}"/>')
    return '\n'.join(html_bits)

def get_html(result: Result, style_spec: StyleSpec) -> str:
    tpl = """\
    <style>
        {{generic_unstyled_css}}
        {{styled_stats_tbl_css}}
    </style>

    <div class='default'>
    <h2>{{ title }}</h2>
    <p>p value {{ p_text }}<a href='#ft1'><sup>1</sup></a></p>

    <p>Pearson's Chi Square statistic: {{ chi_square }}</p>
    <p>Degrees of Freedom (df) {{ degrees_of_freedom }}</p>

    {{ observed_vs_expected_tbl }}

    <p>Minimum expected cell count: {{ min_count_rounded }}</p>
    <p>&#37; cells with expected count < 5: {{ pct_cells_lt_5_rounded }}</p>

    {% for footnote in footnotes %}
      <p><a id='ft{{ loop.index }}'></a><sup>{{ loop.index }}</sup>{{ footnote }}</p>
    {% endfor %}

    {% if worked_example %}
      {{ worked_example }}
    {% endif %}

    <hr><p>Interpreting the Proportions chart - look at the "All combined" category - the more different the other
    '{{ variable_a_name }}' categories look from this the more likely the Chi Square test will detect a difference.
    Within each '{{ variable_b_name }}' category the '{{ variable_b_name }}' values add up to 1 i.e. 100%.
    This is not the same way of displaying data as a clustered bar chart although the similarity can be confusing.</p>

    {{ chi_square_charts }}   

    </div>
    """
    dp = result.decimal_points
    generic_unstyled_css = get_generic_unstyled_css()
    styled_stats_tbl_css = get_styled_stats_tbl_css(style_spec)
    title = (f"Results of Pearson's Chi Square Test of Association "
        f'Between "{result.variable_a_name}" and "{result.variable_b_name}"')

    p_text = get_p(result.p)
    chi_square = round(result.chi_square, dp)

    p_explain = get_p_explain(result.variable_a_name, result.variable_b_name)
    one_tail_explain = ("This is a one-tailed result "
        "i.e. based on the likelihood of a difference in one particular direction")
    p_full_explanation = f"{p_explain}</br></br>{one_tail_explain}"

    min_count_rounded = round(result.minimum_cell_count, dp)
    pct_cells_lt_5_rounded = round(result.pct_cells_lt_5, 1)

    context = {
        'generic_unstyled_css': generic_unstyled_css,
        'styled_stats_tbl_css': styled_stats_tbl_css,
        'title': title,

        'chi_square_charts': result.chi_square_charts,
        'chi_square': chi_square,
        'degrees_of_freedom': result.degrees_of_freedom,
        'footnotes': [p_full_explanation, ],
        'min_count_rounded': min_count_rounded,
        'observed_vs_expected_tbl': result.observed_vs_expected_tbl,
        'p_text': p_text,
        'pct_cells_lt_5_rounded': pct_cells_lt_5_rounded,
        'variable_a_name': result.variable_a_name,
        'variable_b_name': result.variable_b_name,
        'worked_example': result.worked_example,
    }
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return html


@dataclass(frozen=False)
class ChiSquareDesign(CommonDesign):
    variable_a_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY
    variable_b_name: str = DEFAULT_SUPPLIED_BUT_MANDATORY_ANYWAY

    show_workings: bool = False

    def to_result(self) -> ChiSquareResult:
        ## data
        chi_square_data = get_chi_square_data(cur=self.cur, dbe_spec=self.dbe_spec,
            source_table_name=self.source_table_name, table_filter_sql=self.table_filter_sql,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            sort_orders=self.sort_orders)
        ## get results
        stats_result = chi_square_stats_calc(
            f_obs=chi_square_data.observed_values_a_then_b_ordered,
            f_exp=chi_square_data.expected_values_a_then_b_ordered,
            df=chi_square_data.degrees_of_freedom)
        return stats_result

    def to_html_design(self) -> HTMLItemSpec:
        ## style
        style_spec = get_style_spec(style_name=self.style_name)
        ## data
        chi_square_data = get_chi_square_data(cur=self.cur, dbe_spec=self.dbe_spec,
            source_table_name=self.source_table_name, table_filter_sql=self.table_filter_sql,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            sort_orders=self.sort_orders)
        ## get results
        stats_result = chi_square_stats_calc(
            f_obs=chi_square_data.observed_values_a_then_b_ordered,
            f_exp=chi_square_data.expected_values_a_then_b_ordered,
            df=chi_square_data.degrees_of_freedom)

        observed_vs_expected_tbl = get_observed_vs_expected_tbl(
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            variable_a_values=chi_square_data.variable_a_values, variable_b_values=chi_square_data.variable_b_values,
            observed_values_a_then_b_ordered=chi_square_data.observed_values_a_then_b_ordered,
            expected_values_a_then_b_ordered=chi_square_data.expected_values_a_then_b_ordered,
            style_name_hyphens=style_spec.style_name_hyphens,
        )

        chi_square_charts = get_chi_square_charts(
            style_spec=style_spec,
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            variable_a_values=chi_square_data.variable_a_values, variable_b_values=chi_square_data.variable_b_values,
            observed_values_a_then_b_ordered=chi_square_data.observed_values_a_then_b_ordered)

        if self.show_workings:
            worked_result = get_worked_result(
                variable_a_values=chi_square_data.variable_a_values, variable_b_values=chi_square_data.variable_b_values,
                observed_values_a_then_b_ordered=chi_square_data.observed_values_a_then_b_ordered,
                degrees_of_freedom=chi_square_data.degrees_of_freedom)
            worked_example = get_worked_example(worked_result)
        else:
            worked_result = None
            worked_example = ''
        result = Result(
            variable_a_name=self.variable_a_name, variable_b_name=self.variable_b_name,
            variable_a_values=chi_square_data.variable_a_values, variable_b_values=chi_square_data.variable_b_values,
            observed_values_a_then_b_ordered=chi_square_data.observed_values_a_then_b_ordered,
            expected_values_a_then_b_ordered=chi_square_data.expected_values_a_then_b_ordered,
            p=stats_result.p, chi_square=stats_result.chi_square, degrees_of_freedom=chi_square_data.degrees_of_freedom,
            minimum_cell_count=chi_square_data.minimum_cell_count, pct_cells_lt_5=chi_square_data.pct_cells_freq_under_5,
            observed_vs_expected_tbl=observed_vs_expected_tbl, chi_square_charts=chi_square_charts,
            worked_example=worked_example, decimal_points=self.decimal_points,
        )
        html = get_html(result, style_spec)
        return HTMLItemSpec(
            html_item_str=html,
            style_name=self.style_name,
            output_item_type=OutputItemType.STATS,
        )


# if __name__ == '__main__':
#     from itertools import product
#     from random import randint
#     a_vals = ['cat', 'dog', ]
#     b_vals = ['apple', 'banana', 'cherry', ]
#     data = []
#     for a_val, b_val in product(a_vals, b_vals):
#         n_rows = randint(15, 100)
#         rows = [(a_val, b_val) for _i in range(n_rows)]
#         data.extend(rows)
#     df = pd.DataFrame(data, columns=['pet', 'fruit'])
#     print(chi_square_from_df(df))
