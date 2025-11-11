"""
CSS needed for header:

General e.g. body - font, background colour etc. (see generic_unstyled_css())

Dojo for charts - want name-spaced CSS for every style in styles folder.
Non-CSS styling, e.g. colour for pie chart slices, already set in JS functions directly.

Tables - only want general table settings in CSS (e.g. spacing) - nothing style-specific.
All specifics styling should be either:

In main output tables via Pandas, non-CSS styling
OR
in simple stats data tables via inline CSS drawing on details directly accessing
and using style-specific values.
"""
from collections.abc import Sequence
from enum import Enum
import importlib

import jinja2
from ruamel.yaml import YAML

from sofastats.conf.main import DOJO_COLOURS, CUSTOM_STYLES_FOLDER
from sofastats.output.styles.interfaces import (
    ChartStyleSpec, ColourWithHighlight, DojoStyleSpec, StyleSpec, TableStyleSpec)
from sofastats.utils.misc import todict

yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)

def yaml_to_style_spec(*, style_name: str, yaml_dict: dict) -> StyleSpec:
    y = yaml_dict
    try:
        table_spec = TableStyleSpec(
            ## font colours
            var_font_colour_first_level=y['var_font_colour_first_level'],
            var_font_colour_not_first_level=y['var_font_colour_not_first_level'],
            heading_footnote_font_colour=y['heading_footnote_font_colour'],
            footnote_font_colour=y['footnote_font_colour'],
            ## background colours
            var_bg_colour_first_level=y['var_bg_colour_first_level'],
            var_bg_colour_not_first_level=y['var_bg_colour_not_first_level'],
            ## borders
            var_border_colour_first_level=y['var_border_colour_first_level'],
            var_border_colour_not_first_level=y['var_border_colour_not_first_level'],
            ## space-holders
            spaceholder_bg_colour=y['spaceholder_bg_colour'],
            spaceholder_bg_img=y.get('spaceholder_bg_img'),
        )
        chart_spec = ChartStyleSpec(
            chart_bg_colour=y['chart_bg_colour'],
            chart_font_colour=y['chart_font_colour'],
            plot_bg_colour=y['plot_bg_colour'],
            plot_font_colour=y['plot_font_colour'],
            plot_bg_colour_filled=y['plot_bg_colour_filled'],
            plot_font_colour_filled=y['plot_font_colour_filled'],
            axis_font_colour=y['axis_font_colour'],
            major_grid_line_colour=y['major_grid_line_colour'],
            grid_line_width=int(y['grid_line_width']),
            stroke_width=int(y['stroke_width']),
            tooltip_border_colour=y['tooltip_border_colour'],
            normal_curve_colour=y['normal_curve_colour'],
            colour_mappings=[
                ColourWithHighlight(y['colour_mappings_0_a'], y['colour_mappings_0_b']),
                ColourWithHighlight(y['colour_mappings_1_a'], y['colour_mappings_1_b']),
                ColourWithHighlight(y['colour_mappings_2_a'], y['colour_mappings_2_b']),
                ColourWithHighlight(y['colour_mappings_3_a'], y['colour_mappings_3_b']),
                ColourWithHighlight(y['colour_mappings_4_a'], y['colour_mappings_4_b']),
            ],
        )
        dojo_spec = DojoStyleSpec(
            connector_style=y['connector_style'],
            tooltip_connector_up=y['tooltip_connector_up'],
            tooltip_connector_down=y['tooltip_connector_down'],
            tooltip_connector_left=y['tooltip_connector_left'],
            tooltip_connector_right=y['tooltip_connector_right'],
        )
    except KeyError as e:
        e.add_note("Unable to extract all required information from YAML - please check all required keys have values")
        raise
    style_spec = StyleSpec(
        name=style_name,
        table=table_spec,
        chart=chart_spec,
        dojo=dojo_spec,
    )
    return style_spec

def get_style_spec(style_name: str, *, debug=False) -> StyleSpec:
    """
    Get dataclass with key colour details and so on e.g.
    style_spec.table_spec.heading_cell_border (DARKER_MID_GREY)
    style_spec.table_spec.first_row_border (None)
    """
    try:
        ## try using a built-in style
        style_module = importlib.import_module(f"sofastats_lib.output.styles.{style_name}")
    except ModuleNotFoundError:
        ## look for custom YAML file
        yaml_fpath = CUSTOM_STYLES_FOLDER / f"{style_name}.yaml"
        try:
            yaml_dict = yaml.load(yaml_fpath)
        except FileNotFoundError as e:
            e.add_note(f"Unable to open {yaml_fpath} to extract style specification for '{style_name}'")
            raise
        except Exception as e:
            e.add_note(f"Experienced a problem extracting style information from '{yaml_fpath}'")
            raise
        else:
            if debug: print(yaml_dict)
            try:
                style_spec = yaml_to_style_spec(style_name=style_name, yaml_dict=yaml_dict)
            except KeyError as e:
                e.add_note(f"Unable to create style spec from '{yaml_fpath}'")
                raise
    else:
        style_spec = style_module.get_style_spec()
    return style_spec

class CSS(Enum):
    """
    CSS can be stored as giant, monolithic blocks of text ready for insertion at the top of HTML files.
    Or as smaller blocks of css stored in variables.
    We store CSS as variables when we need to use it for specific parts of tables in the form of inline CSS.
    In such cases, individual blocks of CSS text are supplied to tables via Pandas df styling.
    Note - CSS text pulled out into individual variables can still be used as part of large, monolithic CSS text
    for insertion at the top of HTML files - it just has to be interpolated in (see generic_unstyled_css()).
    """
    ROW_LEVEL_1_VAR = [
        "font-family: Ubuntu, Helvetica, Arial, sans-serif;",
        "font-weight: bold;",
        "font-size: 14px;"
    ]
    COL_LEVEL_1_VAR = ROW_LEVEL_1_VAR + [
        'padding: 9px 6px;',
        'vertical-align: top;',
    ]
    COL_VALUE = [
        'font-size: 12px;',
        'vertical-align: top;',
    ]
    MEASURE = COL_VALUE
    ROW_VALUE = [
        'margin: 0;',
    ]
    LEFT = [
        'text-align: left;',
    ]
    RIGHT = [
        'text-align: right;',
    ]
    DATA_TBL_TOTAL_ROW = [
        'font-weight: bold;',
        'border-top: solid 2px black;',
        'border-bottom: double 3px black;',
    ]
    DATA_TBL_DATA_CELL = [
        'text-align: right; margin: 0;',
    ]

def get_generic_unstyled_css() -> str:
    """
    Get CSS with no style-specific aspects: includes stats tables, some parts of main tables
    (the rest is tied to individual ids because of how Pandas-based HTML table styling works), Dojo, and page styling.
    """

    def flatten(items: Sequence[str]):
        flattened = '\n'.join(items)
        return flattened

    generic_unstyled_css = f"""\
    body {{
        font-size: 12px;
        font-family: Ubuntu, Helvetica, Arial, sans-serif;
    }}
    h1, h2 {{
        font-family: Ubuntu, Helvetica, Arial, sans-serif;
        font-weight: bold;
    }}
    h1 {{
        font-size: 18px;
    }}
    h2 {{
        font-size: 16px;
    }}
    .page-break-before {{
        page-break-before: always;
        border-bottom: none;
        width: auto;
        height: 18px;
    }}
    table {{
        border-collapse: collapse;
    }}

    /* Main tables are also styled by Pandas - they are styled at the id level <===================================== */

    /* Note - tables are not just used for report tables but also in chart legends and more besides  */
    tr, td, th {{
        margin: 0;
    }}
    tr.data-tbl-data-cell td {{
        {flatten(CSS.DATA_TBL_DATA_CELL.value)}
    }}
    tr.data-tbl-total-row td {{
        {flatten(CSS.DATA_TBL_TOTAL_ROW.value)}
    }}
    th, .data {{
        border: solid 1px #afb2b6; /*dark grey*/
    }}
    th {{
        margin: 0;
        padding: 0px 6px;
    }}
    td {{
        padding: 2px 6px;
        font-size: 13px;
    }}
    td, .data {{
        text-align: right;
    }}
    .row-level-1-var {{
        {flatten(CSS.ROW_LEVEL_1_VAR.value)}
    }}
    .col-level-1-var {{
        {flatten(CSS.COL_LEVEL_1_VAR.value)}
    }}
    .row-value {{
        {flatten(CSS.ROW_VALUE.value)}
    }}
    .col-value {{
        {flatten(CSS.COL_VALUE.value)}
    }}
    .ftnote-line{{
        /* for hr http://www.w3schools.com/TAGS/att_hr_align.asp*/
        width: 300px;
        text-align: left; /* IE and Opera*/
        margin-left: 0; /* Firefox, Chrome, Safari */
    }}
    .left {{
        {flatten(CSS.LEFT.value)}
    }}
    .right {{
        {flatten(CSS.RIGHT.value)}
    }}
    """
    return generic_unstyled_css

def get_styled_dojo_chart_css(dojo_style_spec: DojoStyleSpec) -> str:
    """
    Style-specific DOJO - needed only once even if multiple items with the same style.
    Not needed if style not used.
    Each class contains the connector_style so charts with different styles can coexist in a single report.
    If several styles share connector style there is no conflict - they'll also share the CSS.
    Supplied by the attributes of the DojoStyleSpec.
    """
    tpl = """\
        /* Tool tip connector arrows */
        .dijitTooltipBelow-{{ connector_style }} {
          padding-top: 13px;
        }
        .dijitTooltipAbove-{{ connector_style }} {
          padding-bottom: 13px;
        }
        .tundra .dijitTooltipBelow-{{ connector_style }} .dijitTooltipConnector {
          top: 0px;
          left: 3px;
          background: url("{{ tooltip_connector_up }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipAbove-{{ connector_style }} .dijitTooltipConnector {
          bottom: 0px;
          left: 3px;
          background: url("{{ tooltip_connector_down }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipLeft-{{ connector_style }} {
          padding-right: 14px;
        }
        .tundra .dijitTooltipLeft-{{ connector_style }} .dijitTooltipConnector {
          right: 0px;
          bottom: 3px;
          background: url("{{ tooltip_connector_right }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipRight-{{ connector_style }} {
          padding-left: 14px;
        }
        .tundra .dijitTooltipRight-{{ connector_style }} .dijitTooltipConnector {
          left: 0px;
          bottom: 3px;
          background: url("{{ tooltip_connector_left }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
    """
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    context = todict(dojo_style_spec, shallow=True)
    css = template.render(context)
    return css

def get_long_colour_list(colour_mappings: Sequence[ColourWithHighlight]) -> list[str]:
    defined_colours = [colour_mapping.main for colour_mapping in colour_mappings]
    long_colour_list = defined_colours + DOJO_COLOURS
    return long_colour_list

def _get_bg_line(style_spec: StyleSpec) -> str:
    if style_spec.table.spaceholder_bg_img:
        bg_line = f"background-image: url({style_spec.table.spaceholder_bg_img}) !important;"
    elif style_spec.table.spaceholder_bg_colour:
        bg_line = f"background-color: {style_spec.table.spaceholder_bg_colour};"
    else:
        bg_line = ''
    return bg_line

def get_styled_stats_tbl_css(style_spec: StyleSpec) -> str:
    """
    Note - main table CSS is handled completely separately
    (controlled by Pandas and the spaceholder CSS with embedded image)
    """
    tpl = """\
        .firstcolvar-{{ style_name_hyphens }}, .firstrowvar-{{ style_name_hyphens }}, .spaceholder-{{ style_name_hyphens }} {
            font-family: Ubuntu, Helvetica, Arial, sans-serif;
            font-weight: bold;
            font-size: 14px;
            color: {{ var_font_colour_first_level }};
        }
        .spaceholder-{{ style_name_hyphens }} {
            {{ bg_line }}
        }
        .firstrowvar-{{ style_name_hyphens }} {
            color: {{ var_font_colour_first_level }};
            background-color: {{ var_bg_colour_first_level }};
        }
        .firstcolvar-{{ style_name_hyphens }} {
            padding: 9px 6px;
            vertical-align: top;
            color: {{ var_font_colour_first_level }};
            background-color: {{ var_bg_colour_first_level }};
        }
        td.lbl-{{ style_name_hyphens }} {
            color: {{ var_font_colour_not_first_level }};
            background-color: {{ var_bg_colour_not_first_level }};
        }
        td.{{ style_name_hyphens }}, th.{{ style_name_hyphens }}, td.rowval-{{ style_name_hyphens }}, td.datacell-{{ style_name_hyphens }} {
            border: 1px solid {{ var_border_colour_not_first_level }};
        }
        .tbl-heading-footnote-{{ style_name_hyphens }}{
            color: {{ heading_footnote_font_colour }};
        }
    """
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    context = todict(style_spec.table, shallow=True)
    context['style_name_hyphens'] = style_spec.style_name_hyphens
    bg_line = _get_bg_line(style_spec)
    context['bg_line'] = bg_line
    css = template.render(context)
    return css

def get_styled_placeholder_css_for_main_tbls(style_name: str) -> str:
    """
    Only used in main tables (cross-tab and freq) not in Stats output tables e.g. ANOVA results tables
    """
    style_spec = get_style_spec(style_name)
    bg_line = _get_bg_line(style_spec)
    placeholder_css = """
    .spaceholder-%(style_name_hyphens)s {
        %(bg_line)s
        border: solid 1px %(border)s;
    }
    """ % {
        'style_name_hyphens': style_spec.style_name_hyphens,
        'bg_line': bg_line,
        'border': style_spec.table.var_border_colour_first_level,
    }
    return placeholder_css

if __name__ == '__main__':
    get_style_spec('horrific')
