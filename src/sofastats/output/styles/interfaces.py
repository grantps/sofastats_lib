## No project dependencies :-)
from collections.abc import Sequence
from dataclasses import dataclass

@dataclass(frozen=True)
class ColorWithHighlight:
    main: str
    highlight: str

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
    chart_background_color: str
    chart_title_font_color: str
    plot_background_color: str
    plot_font_color: str
    axis_font_color: str
    major_grid_line_color: str
    grid_line_width: int
    border_width: int
    border_color: str
    tool_tip_border_color: str
    normal_curve_color: str
    color_mappings: Sequence[ColorWithHighlight]

@dataclass(frozen=True)
class DojoStyleSpec:
    connector_style: str
    tool_tip_connector_up: str
    tool_tip_connector_down: str
    tool_tip_connector_left: str
    tool_tip_connector_right: str

@dataclass(frozen=True)
class StyleSpec:
    name: str
    table: TableStyleSpec
    chart: ChartStyleSpec
    dojo: DojoStyleSpec

    @property
    def style_name_hyphens(self):
        return self.name.replace('_', '-')
