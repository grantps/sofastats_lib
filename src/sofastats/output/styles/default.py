from sofastats.conf.images import (
    TOOLTIPCONNECTORDOWN_DEFBROWN, TOOLTIPCONNECTORUP_DEFBROWN, TOOLTIPCONNECTORLEFT_DEFBROWN, TOOLTIPCONNECTORRIGHT_DEFBROWN)
from sofastats.output.styles.interfaces import (
    ChartStyleSpec, ColourWithHighlight, DojoStyleSpec, StyleSpec, TableStyleSpec)

BLACK_BLUE = '#333435'
BLACK_BROWN = '#423126'
LIGHT_GREY_BLUE = '#f2f1f0'
LIGHT_GREY = '#f5f5f5'
GREY_BLUE = '#ccd9d7'
MID_GREY_BROWN = '#b8a49e'
MID_GREY = '#c0c0c0'
DARKER_MID_GREY = '#a1a1a1'
CHARCOAL_BROWN = '#736354'
BURNT_ORANGE = '#e95f29'
ORANGE = '#ef7d44'
YORANGE = '#f4cb3a'
PALE_YORANGE = '#f7d858'
BLUE_TURQUOISE = '#4495c3'
TURQUOISE = '#62add2'
DARK_GREEN = '#44953a'
GREEN = '#62ad58'
OFF_SCARLET = '#f43a3a'
PALE_SCARLET = '#f75858'
WHITE = '#ffffff'
BLACK = '#000000'

def get_style_spec() -> StyleSpec:
    connector_style = 'defbrown'
    table_spec = TableStyleSpec(
        ## font colours
        var_font_colour_first_level=WHITE,
        var_font_colour_not_first_level=BLACK_BLUE,
        heading_footnote_font_colour=WHITE,
        footnote_font_colour=BLACK,
        ## background colours
        var_bg_colour_first_level=BLACK_BLUE,
        var_bg_colour_not_first_level=LIGHT_GREY,
        ## borders
        var_border_colour_first_level=DARKER_MID_GREY,
        var_border_colour_not_first_level=MID_GREY,
        ## space-holders
        spaceholder_bg_colour=GREY_BLUE,
        spaceholder_bg_img=None,
    )
    chart_spec = ChartStyleSpec(
        chart_bg_colour=WHITE,
        chart_font_colour=BLACK_BROWN,
        plot_bg_colour=LIGHT_GREY_BLUE,
        plot_font_colour=BLACK_BROWN,
        plot_bg_colour_filled=LIGHT_GREY_BLUE,
        plot_font_colour_filled=BLACK_BROWN,
        axis_font_colour=BLACK_BROWN,
        major_grid_line_colour=MID_GREY_BROWN,
        grid_line_width=1,
        stroke_width=3,
        tooltip_border_colour=CHARCOAL_BROWN,
        normal_curve_colour=BLACK_BROWN,
        colour_mappings=[
            ColourWithHighlight(BURNT_ORANGE, ORANGE),
            ColourWithHighlight(YORANGE, PALE_YORANGE),
            ColourWithHighlight(BLUE_TURQUOISE, TURQUOISE),
            ColourWithHighlight(DARK_GREEN, GREEN),
            ColourWithHighlight(OFF_SCARLET, PALE_SCARLET),
        ],
    )
    dojo_spec = DojoStyleSpec(
        connector_style=connector_style,
        tooltip_connector_up=TOOLTIPCONNECTORUP_DEFBROWN,
        tooltip_connector_down=TOOLTIPCONNECTORDOWN_DEFBROWN,
        tooltip_connector_left=TOOLTIPCONNECTORLEFT_DEFBROWN,
        tooltip_connector_right=TOOLTIPCONNECTORRIGHT_DEFBROWN,
    )
    style_spec = StyleSpec(
        name='default',
        table=table_spec,
        chart=chart_spec,
        dojo=dojo_spec,
    )
    return style_spec
