from collections.abc import Sequence

from sofastats_lib import logger
from sofastats_lib.conf.main import (AVG_CHAR_WIDTH_PIXELS, AVG_LINE_HEIGHT_PIXELS, DOJO_Y_AXIS_TITLE_OFFSET,
    MAX_SAFE_X_LBL_LEN_PIXELS)
from sofastats_lib.data_extraction.charts.interfaces import CategorySpec
from sofastats_lib.output.charts.interfaces import LeftMarginOffsetSpec

def get_left_margin_offset(*, width_after_left_margin: float, offsets: LeftMarginOffsetSpec,
        is_multi_chart: bool, y_axis_title_offset: float, rotated_x_lbls: bool) -> float:
    wide = width_after_left_margin > 1_200
    initial_offset = offsets.wide_offset if wide else offsets.initial_offset  ## otherwise gets squeezed out e.g. in pct
    offset = initial_offset + y_axis_title_offset - DOJO_Y_AXIS_TITLE_OFFSET
    offset = offset + offsets.rotate_offset if rotated_x_lbls else offset
    offset = offset + offsets.multi_chart_offset if is_multi_chart else offset
    return offset

def get_x_axis_font_size(*, n_x_items: int, is_multi_chart: bool) -> float:
    if n_x_items <= 5:
        x_axis_font_size = 10
    elif n_x_items > 10:
        x_axis_font_size = 8
    else:
        x_axis_font_size = 9
    x_axis_font_size = x_axis_font_size * 0.75 if is_multi_chart else x_axis_font_size
    return x_axis_font_size

def get_height(*, axis_lbl_drop: float, rotated_x_lbls=False, max_x_axis_lbl_len: float) -> float:
    height = 310
    if rotated_x_lbls:
        height += AVG_CHAR_WIDTH_PIXELS * max_x_axis_lbl_len
    height += axis_lbl_drop  ## compensate for loss of bar display height
    return height

def get_axis_lbl_drop(*, is_multi_chart: bool, rotated_x_lbls: bool, max_x_axis_lbl_lines: int) -> int:
    axis_lbl_drop = 10 if is_multi_chart else 15
    if not rotated_x_lbls:
        extra_lines = max_x_axis_lbl_lines - 1
        axis_lbl_drop += AVG_LINE_HEIGHT_PIXELS * extra_lines
    logger.debug(axis_lbl_drop)
    return axis_lbl_drop

def get_y_axis_title_offset(*, x_axis_title_len: int, rotated_x_lbls=False) -> int:
    """
    Need to shift y-axis title left by y_axis_title_offset if first x-axis label is wide.
    """
    ## 45 is a good total offset with label width of 20
    y_axis_title_offset = DOJO_Y_AXIS_TITLE_OFFSET - 20  ## e.g. 20
    ## first x-axis label adjustment
    horizontal_x_lbls = not rotated_x_lbls
    if horizontal_x_lbls:
        if x_axis_title_len * AVG_CHAR_WIDTH_PIXELS > MAX_SAFE_X_LBL_LEN_PIXELS:
            lbl_width_shifting = (x_axis_title_len * AVG_CHAR_WIDTH_PIXELS) - MAX_SAFE_X_LBL_LEN_PIXELS
            lbl_shift = lbl_width_shifting / 2  ## half of label goes to the right
            y_axis_title_offset += lbl_shift
    y_axis_title_offset = max([y_axis_title_offset, DOJO_Y_AXIS_TITLE_OFFSET])
    return y_axis_title_offset

def get_x_axis_lbls_val_and_text(x_axis_specs: Sequence[CategorySpec]) -> list[str]:
    """
    Note - can be a risk that a split label for the middle x value will overlap with x-axis label below
    """
    lbls_val_and_text = []
    for n, x_axis_spec in enumerate(x_axis_specs, 1):
        lbls_val_and_text.append(f'{{value: {n}, text: "{x_axis_spec.lbl}"}}')
    return lbls_val_and_text
