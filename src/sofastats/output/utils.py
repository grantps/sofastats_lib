import base64
from collections.abc import Sequence
from io import BytesIO
import math
from pathlib import Path

import jinja2

from sofastats.output.charts.conf import DOJO_CHART_JS
from sofastats.output.interfaces import (
    BODY_AND_HTML_END_TPL, BODY_START_TPL, CHARTING_CSS_TPL, DOJO_XD_JS, HEAD_END_TPL, HTML_AND_SOME_HEAD_TPL,
    SOFASTATS_CHARTS_JS, SOFASTATS_DOJO_MINIFIED_JS, SPACEHOLDER_CSS_TPL, STATS_TBL_TPL, TUNDRA_CSS,
    HasToHTMLItemSpec, OutputItemType, Report)
from sofastats.output.styles.utils import (get_generic_unstyled_css, get_style_spec, get_styled_dojo_chart_css,
    get_styled_placeholder_css_for_main_tbls, get_styled_stats_tbl_css)

def image_as_data(image_file_path: Path) -> str:
    """
    Returns data:image ...
    """
    binary_fc = open(image_file_path, 'rb').read()  ## fc a.k.a. file_content
    img_base64 = base64.b64encode(binary_fc).decode('utf-8')
    image_as_data_str = f"data:image/gif;base64,{img_base64}"
    return image_as_data_str

def plot2image_as_data(plot) -> str:
    """
    Args:
        plot: plot (save) or fig (savefig)
    Returns: "data:image ..."
    """
    b_io_1 = BytesIO()
    try:
        plot.save(b_io_1)  ## save to a fake file
    except AttributeError:
        plot.savefig(b_io_1)
    chart_base64_1 = base64.b64encode(b_io_1.getvalue()).decode('utf-8')
    image_as_data_str = f'data:image/png;base64,{chart_base64_1}'
    return image_as_data_str

def get_report(designs: Sequence[HasToHTMLItemSpec], title: str, *, is_gallery=False) -> Report:
    """
    Collectively work out all which unstyled and styled CSS / JS items are needed in HTML.
    Then, in body, put the HTML strs in order.
    Aligning param names exactly with templates from output.interfaces

    HTMLItemSpec.to_standalone_html() also handles final HTML output
    """
    tpl_bits = [
        HTML_AND_SOME_HEAD_TPL,  ## unstyled
    ]
    context = {
        'tundra_css': TUNDRA_CSS,
        'dojo_xd_js': DOJO_XD_JS,
        'sofastats_charts_js': SOFASTATS_CHARTS_JS,
        'sofastats_dojo_minified_js': SOFASTATS_DOJO_MINIFIED_JS,
        'generic_unstyled_css': get_generic_unstyled_css(),
        'title': title,
    }
    if is_gallery:
        context['gallery_css'] = """
        h1.toc-heading {
          font-size: 24px;
        }
        h2.toc-heading {
          font-size: 20px;
        }

        a.toc-link {
          font-weight: bold;
          font-size: 18px;
        }
        a.toc-link:link, a.toc-link:visited, a.toc-link:focus {
          text-decoration: none;
          color: #3465a4;
        }
        a.toc-link:hover {
          text-decoration: underline;
          color: #3465a4;
        }
        a.toc-link:active {
          text-decoration: none;
          color: #3465a4;
        }

        a#return-to-origin {
          font-weight: bold;
          font-size: 22px;
        }
        a#return-to-origin:link, a#return-to-origin:visited, a#return-to-origin:focus {
          text-decoration: none;
          color: #3465a4;
        }
        a#return-to-origin:hover {
          text-decoration: underline;
          color: #3465a4;
        }
        a#return-to-origin:active {
          text-decoration: none;
          color: #3465a4;
        }

        .item-heading {
          margin-bottom: 12px;
        }
        """
    html_item_specs = [design.to_html_design() for design in designs]
    ## CHARTS
    includes_charts = False
    for html_item_spec in html_item_specs:
        if html_item_spec.output_item_type==OutputItemType.CHART:
            includes_charts = True
            break
    if includes_charts:
        ## unstyled
        tpl_bits.append(DOJO_CHART_JS)
        ## styled
        chart_styles_done = set()
        for html_item_spec in html_item_specs:
            if html_item_spec.output_item_type==OutputItemType.CHART and html_item_spec.style_name not in chart_styles_done:
                styled_css_context_param = f'{html_item_spec.style_name}_styled_dojo_chart_css'
                styled_charting_css_tpl = (CHARTING_CSS_TPL
                    .replace('styled_dojo_chart_css', styled_css_context_param)
                )
                tpl_bits.append(styled_charting_css_tpl)
                style_spec = get_style_spec(html_item_spec.style_name)
                context[styled_css_context_param] = get_styled_dojo_chart_css(style_spec.dojo)
                chart_styles_done.add(html_item_spec.style_name)
    ## STATS
    includes_stats = False
    for html_item_spec in html_item_specs:
        if html_item_spec.output_item_type==OutputItemType.STATS:
            includes_stats = True
            break
    if includes_stats:
        ## styled
        stats_styles_done = set()
        for html_item_spec in html_item_specs:
            if (html_item_spec.output_item_type==OutputItemType.STATS
                    and html_item_spec.style_name not in stats_styles_done):
                styled_stats_tbl_context_param = f'{html_item_spec.style_name}_styled_stats_tbl_css'
                styled_stats_tbl_tpl = STATS_TBL_TPL.replace('styled_stats_tbl_css', styled_stats_tbl_context_param)
                tpl_bits.append(styled_stats_tbl_tpl)
                style_spec = get_style_spec(html_item_spec.style_name)
                context[styled_stats_tbl_context_param] = get_styled_stats_tbl_css(style_spec)
                stats_styles_done.add(html_item_spec.style_name)
    ## MAIN TABLES
    includes_main_tbls = False
    for html_item_spec in html_item_specs:
        if html_item_spec.output_item_type==OutputItemType.MAIN_TABLE:
            includes_main_tbls = True
            break
    if includes_main_tbls:
        ## styled
        tbl_styles_done = set()
        for html_item_spec in html_item_specs:
            if (html_item_spec.output_item_type==OutputItemType.MAIN_TABLE
                    and html_item_spec.style_name not in tbl_styles_done):
                styled_spaceholder_context_param = f'{html_item_spec.style_name}_styled_placeholder_css_for_main_tbls'
                styled_spaceholder_css_tpl = SPACEHOLDER_CSS_TPL.replace(
                    'styled_placeholder_css_for_main_tbls', styled_spaceholder_context_param)
                tpl_bits.append(styled_spaceholder_css_tpl)
                context[styled_spaceholder_context_param] = get_styled_placeholder_css_for_main_tbls(
                    html_item_spec.style_name)
                tbl_styles_done.add(html_item_spec.style_name)
    ## unstyled & already styled
    tpl_bits.append(HEAD_END_TPL)
    tpl_bits.append(BODY_START_TPL)
    if is_gallery:
        toc_html = ("<h2 id='__contents__' class='toc-heading'>Contents</h2>"
            + "<br>".join(
                    (f"<a class='toc-link' href='#{html_item_spec.output_title}'>"
                     f"{html_item_spec.output_title} ({html_item_spec.design_name})"
                     "</a>")
                for html_item_spec in html_item_specs))
        toc_or_not = '\n' + toc_html
    else:
        toc_or_not = ''
    items = []
    for html_item_spec in html_item_specs:
        if is_gallery:
            back_to_contents = " <a class='toc-link' href='#__contents__'>Back to Contents</a>"
        else:
            back_to_contents = ''
        item = (f"<hr><div class='item-heading'><h2 class='toc-heading' id='{html_item_spec.output_title}'>"
            f"{html_item_spec.output_title} ({html_item_spec.design_name})</h2>{back_to_contents}</div>"
            f"\n{html_item_spec.html_item_str}")
        items.append(item)  ## <======= the actual item content as HTML e.g. for a bar chart
    items_html = """"<br><div style="clear: both;"></div><br>""".join(items)
    if is_gallery:
        return_html_or_not = (
            f"<a id='return-to-origin' href='https://sofastats.github.io/sofastats_lib'>Back to sofastats main menu</a>\n")
    else:
        return_html_or_not = ""
    tpl_bits.append(f"<h1 class='toc-heading'>{title}</h1>\n{return_html_or_not}{toc_or_not}" + items_html)
    tpl_bits.append(BODY_AND_HTML_END_TPL)
    ## assemble
    tpl = '\n'.join(tpl_bits)
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    html = template.render(context)
    return Report(html)

def to_precision(num, precision):
    """
    Returns a string representation of x formatted with a precision of p.

    Based on the webkit JavaScript implementation taken from here:
    https://code.google.com/p/webkit-mirror/source/browse/JavaScriptCore/kjs/number_object.cpp

    http://randlet.com/blog/python-significant-figures-format/
    """
    x = float(num)
    if x == 0.:
        return '0.' + '0'*(precision - 1)
    out = []
    if x < 0:
        out.append('-')
        x = -x
    e = int(math.log10(x))
    tens = math.pow(10, e - precision + 1)
    n = math.floor(x/tens)
    if n < math.pow(10, precision - 1):
        e = e -1
        tens = math.pow(10, e - precision + 1)
        n = math.floor(x / tens)
    if abs((n + 1.) * tens - x) <= abs(n * tens -x):
        n = n + 1
    if n >= math.pow(10, precision):
        n = n / 10.
        e = e + 1
    m = '%.*g' % (precision, n)
    if e < -2 or e >= precision:
        out.append(m[0])
        if precision > 1:
            out.append('.')
            out.extend(m[1:precision])
        out.append('e')
        if e > 0:
            out.append('+')
        out.append(str(e))
    elif e == (precision -1):
        out.append(m)
    elif e >= 0:
        out.append(m[:e+1])
        if e+1 < len(m):
            out.append('.')
            out.extend(m[e+1:])
    else:
        out.append('0.')
        out.extend(['0'] * -(e+1))
        out.append(m)
    return ''.join(out)

def get_p(p):
    p_str = to_precision(num=p, precision=4)
    if p < 0.001:
        p_str = f'< 0.001 ({p_str})'
    return p_str

def format_num(num):
    try:
        formatted = f'{num:,}'
    except ValueError:
        formatted = num
    return formatted

def get_p_explain(a: str, b: str) -> str:
    p_explain = ("If p is small, e.g. less than 0.01, or 0.001, you can assume the result is statistically significant "
     f'i.e. there is a relationship between "{a}" and "{b}". '
     "Note: a statistically significant difference may not necessarily be of any practical significance.")
    return p_explain
