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
from itertools import count
from pathlib import Path
from textwrap import dedent

import jinja2
from ruamel.yaml import YAML

from sofastats.conf.main import DOJO_COLORS, CUSTOM_STYLES_FOLDER
import sofastats.output.styles as styles
from sofastats.output.styles.interfaces import (
    ChartStyleSpec, ColorWithHighlight, DojoStyleSpec, StyleSpec, TableStyleSpec)
from sofastats.utils.misc import todict

yaml = YAML(typ='safe')  ## default, if not specified, is 'rt' (round-trip)

def yaml_to_style_spec(*, style_name: str, yaml_dict: dict) -> StyleSpec:
    y = yaml_dict
    try:
        table_spec = TableStyleSpec(
            ## font colours
            first_level_variable_font_color=y['first_level_variable_font_color'],
            variable_font_color_other_levels=y['variable_font_color_other_levels'],
            heading_footnote_font_color=y['heading_footnote_font_color'],
            footnote_font_color=y['footnote_font_color'],
            ## background colours
            first_level_variable_background_color=y['first_level_variable_background_color'],
            variable_background_color_other_levels=y['variable_background_color_other_levels'],
            ## borders
            first_level_variable_border_color=y['first_level_variable_border_color'],
            variable_border_color_other_levels=y['variable_border_color_other_levels'],
            ## space-holders
            top_left_table_space_holder_background_color=y['top_left_table_space_holder_background_color'],
            top_left_table_space_holder_background_image=y.get('top_left_table_space_holder_background_image'),
        )

        color_mappings = []
        for n in count(1):
            try:
                main_color = y[f'item_{n}_main_color']
                hover_color = y[f'item_{n}_hover_color']
            except KeyError:
                break
            else:
                color_mappings.append(ColorWithHighlight(main_color, hover_color))
        chart_spec = ChartStyleSpec(
            chart_background_color=y['chart_background_color'],
            chart_title_font_color=y['chart_title_font_color'],
            plot_background_color=y['plot_background_color'],
            plot_font_color=y['plot_font_color'],
            axis_font_color=y['axis_font_color'],
            major_grid_line_color=y['major_grid_line_color'],
            grid_line_width=int(y['grid_line_width']),
            border_width=int(y['border_width']),
            border_color=y['border_color'],
            tool_tip_border_color=y['tool_tip_border_color'],
            normal_curve_color=y['normal_curve_color'],
            color_mappings=color_mappings,
        )

        dojo_spec = DojoStyleSpec(
            connector_style=y['connector_style'],
            tool_tip_connector_up=y['tool_tip_connector_up'],
            tool_tip_connector_down=y['tool_tip_connector_down'],
            tool_tip_connector_left=y['tool_tip_connector_left'],
            tool_tip_connector_right=y['tool_tip_connector_right'],
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
    ## try using a built-in style
    built_in_styles_path = Path(styles.__file__).parent
    yaml_fpath = built_in_styles_path / f"{style_name}.yaml"
    if not yaml_fpath.exists():
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
    return style_spec

class CSS(Enum):
    """
    CSS can be stored as giant, monolithic blocks of text ready for insertion at the top of HTML files.
    Or as smaller blocks of CSS stored in variables.
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
          background: url("{{ tool_tip_connector_up }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipAbove-{{ connector_style }} .dijitTooltipConnector {
          bottom: 0px;
          left: 3px;
          background: url("{{ tool_tip_connector_down }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipLeft-{{ connector_style }} {
          padding-right: 14px;
        }
        .tundra .dijitTooltipLeft-{{ connector_style }} .dijitTooltipConnector {
          right: 0px;
          bottom: 3px;
          background: url("{{ tool_tip_connector_right }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
        .tundra .dijitTooltipRight-{{ connector_style }} {
          padding-left: 14px;
        }
        .tundra .dijitTooltipRight-{{ connector_style }} .dijitTooltipConnector {
          left: 0px;
          bottom: 3px;
          background: url("{{ tool_tip_connector_left }}") no-repeat top left !important;
          width: 16px;
          height: 14px;
        }
    """
    environment = jinja2.Environment()
    template = environment.from_string(tpl)
    context = todict(dojo_style_spec, shallow=True)
    css = template.render(context)
    return css

def get_long_color_list(color_mappings: Sequence[ColorWithHighlight]) -> list[str]:
    defined_colors = [color_mapping.main for color_mapping in color_mappings]
    long_color_list = defined_colors + DOJO_COLORS
    return long_color_list

def _get_bg_line(style_spec: StyleSpec) -> str:
    if style_spec.table.top_left_table_space_holder_background_image:
        bg_line = f"background-image: url({style_spec.table.top_left_table_space_holder_background_image}) !important;"
    elif style_spec.table.top_left_table_space_holder_background_color:
        bg_line = f"background-color: {style_spec.table.top_left_table_space_holder_background_color};"
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
            color: {{ first_level_variable_font_color }};
        }
        .spaceholder-{{ style_name_hyphens }} {
            {{ bg_line }}
        }
        .firstrowvar-{{ style_name_hyphens }} {
            color: {{ first_level_variable_font_color }};
            background-color: {{ first_level_variable_background_color }};
        }
        .firstcolvar-{{ style_name_hyphens }} {
            padding: 9px 6px;
            vertical-align: top;
            color: {{ first_level_variable_font_color }};
            background-color: {{ first_level_variable_background_color }};
        }
        td.lbl-{{ style_name_hyphens }} {
            color: {{ variable_font_color_other_levels }};
            background-color: {{ variable_background_color_other_levels }};
        }
        td.{{ style_name_hyphens }}, th.{{ style_name_hyphens }}, td.rowval-{{ style_name_hyphens }}, td.datacell-{{ style_name_hyphens }} {
            border: 1px solid {{ variable_border_color_other_levels }};
        }
        .tbl-heading-footnote-{{ style_name_hyphens }}{
            color: {{ heading_footnote_font_color }};
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
        'border': style_spec.table.first_level_variable_border_color,
    }
    return placeholder_css

def fix_default_single_color_mapping(color_mappings: Sequence[ColorWithHighlight]) -> list[ColorWithHighlight]:
    new_color_mappings = color_mappings[:1]  ## only need the first
    ## This is an important special case because it affects the bar charts using the default style
    if new_color_mappings[0].main.lower() == '#e95f29':  ## BURNT_ORANGE
        new_color_mappings = [ColorWithHighlight('#e95f29', '#736354'), ]
    return new_color_mappings

def get_js_highlighting_function(*,
        color_mappings: Sequence[ColorWithHighlight], chart_uuid: str, uses_faint_version=False) -> str:
    """
    Used to do this in the jinja template but this is centralised and easier to document etc.

    Args:
        uses_faint_version: if True, uses JavaScript getfainthex() on the colours before using them to fill the boxes.
          No point mapping highlight without first converting to the faint versions.
    """
    bits = [
        f"var highlight_{chart_uuid} = function(colour){{",
        "var hlColour;",
        "switch (colour.toHex()){",
    ]
    bits = []
    for color_mapping in color_mappings:
        if uses_faint_version:
            bits.append(f'        case getfainthex("{color_mapping.main.lower()}").toHex(): hlColour = getfainthex("{color_mapping.highlight.lower()}").toHex(); break;')
        else:
            bits.append(f'        case "{color_mapping.main.lower()}": hlColour = "{color_mapping.highlight.lower()}"; break;')
    cases = '\n'.join(bits)
    highlighting_function = (dedent(f"""\
    var highlight_{chart_uuid} = function(colour){{
        var hlColour;
        switch (colour.toHex()){{\n""")
    + cases  ## the default highlighting uses a standard highlight function (usually makes a fainter version of the colour)
    + (f"""
        default: hlColour = hl(colour.toHex()); break;
    }}
    return new dojox.color.Color(hlColour);\n}}"""))
    return highlighting_function

if __name__ == '__main__':
    pass
    # get_style_spec('horrific')
