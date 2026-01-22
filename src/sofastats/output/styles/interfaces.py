## No project dependencies :-)
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

@dataclass(frozen=True)
class ColorWithHighlight:
    main: str
    highlight: str

class ColorShiftJSFunctionName(StrEnum):
    FAINT = 'getFaintHex'
    BRIGHT = 'getBrightHex'
    HALF_BRIGHT = 'getHalfBrightHex'

@dataclass(frozen=False, kw_only=True)  ## unfrozen so post init possible
class TableStyleSpec:
    ## font colours
    first_level_variable_font_color: str
    variable_font_color_other_levels: str
    heading_footnote_font_color: str
    footnote_font_color: str
    ## background colours
    first_level_variable_background_color: str
    variable_background_color_other_levels: str
    ## borders
    first_level_variable_border_color: str  ## usually dark enough for heading cell and spaceholder colours (if they're dark, this must be dark)
    variable_border_color_other_levels: str  ## usually more pale so numbers stand out
    ## space-holders
    top_left_table_space_holder_background_color: str | None = None
    top_left_table_space_holder_background_image: str | None = None

@dataclass(frozen=True)
class ChartStyleSpec:
    axis_font_color: str
    border_color: str
    border_width: int
    chart_background_color: str
    chart_title_font_color: str
    color_mappings: Sequence[ColorWithHighlight]
    grid_line_width: int
    major_grid_line_color: str
    normal_curve_color: str
    plot_background_color: str
    plot_font_color: str
    tool_tip_border_color: str

def _fix_name_for_js(raw_name: str) -> str:
    return raw_name.replace('_', '-').replace(' ', '-').replace('(', '').replace(')', '')

@dataclass(frozen=False)
class DojoStyleSpec:
    style_name: str
    tool_tip_name: str = field(init=False)
    tool_tip_pointer_up: str
    tool_tip_pointer_down: str
    tool_tip_pointer_left: str
    tool_tip_pointer_right: str

    def __post_init__(self):
        self.tool_tip_name = _fix_name_for_js(self.style_name)

@dataclass(frozen=True)
class StyleSpec:
    name: str
    table: TableStyleSpec
    chart: ChartStyleSpec
    dojo: DojoStyleSpec

    @property
    def style_name_hyphens(self):
        return _fix_name_for_js( self.name)
