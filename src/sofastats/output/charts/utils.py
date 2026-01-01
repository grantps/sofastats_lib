from collections.abc import Sequence
from typing import Any

from sofastats import logger
from sofastats.conf.main import (AVG_CHAR_WIDTH_PIXELS, AVG_LINE_HEIGHT_PIXELS, DOJO_Y_AXIS_TITLE_OFFSET,
    MAX_SAFE_X_LBL_LEN_PIXELS)
from sofastats.output.charts.interfaces import LeftMarginOffsetSpec

def get_left_margin_offset(*, width_after_left_margin: float, offsets: LeftMarginOffsetSpec,
        is_multi_chart: bool, y_axis_title_offset: float, rotated_x_labels: bool) -> float:
    wide = width_after_left_margin > 1_200
    initial_offset = offsets.wide_offset if wide else offsets.initial_offset  ## otherwise gets squeezed out e.g. in pct
    offset = initial_offset + y_axis_title_offset - DOJO_Y_AXIS_TITLE_OFFSET
    offset = offset + offsets.rotate_offset if rotated_x_labels else offset
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

def get_height(*, axis_label_drop: float, rotated_x_labels=False, max_x_axis_label_len: float) -> float:
    height = 310
    if rotated_x_labels:
        height += AVG_CHAR_WIDTH_PIXELS * max_x_axis_label_len
    height += axis_label_drop  ## compensate for loss of bar display height
    return height

def get_axis_label_drop(*, is_multi_chart: bool, rotated_x_labels: bool, max_x_axis_label_lines: int) -> int:
    axis_label_drop = 10 if is_multi_chart else 15
    if not rotated_x_labels:
        extra_lines = max_x_axis_label_lines - 1
        axis_label_drop += AVG_LINE_HEIGHT_PIXELS * extra_lines
    logger.debug(axis_label_drop)
    return axis_label_drop

def get_y_axis_title_offset(*, x_axis_title_len: int, rotated_x_labels=False) -> int:
    """
    Need to shift y-axis title left by y_axis_title_offset if first x-axis label is wide.
    """
    ## 45 is a good total offset with label width of 20
    y_axis_title_offset = DOJO_Y_AXIS_TITLE_OFFSET - 20  ## e.g. 20
    ## first x-axis label adjustment
    horizontal_x_labels = not rotated_x_labels
    if horizontal_x_labels:
        if x_axis_title_len * AVG_CHAR_WIDTH_PIXELS > MAX_SAFE_X_LBL_LEN_PIXELS:
            label_width_shifting = (x_axis_title_len * AVG_CHAR_WIDTH_PIXELS) - MAX_SAFE_X_LBL_LEN_PIXELS
            label_shift = label_width_shifting / 2  ## half of label goes to the right
            y_axis_title_offset += label_shift
    y_axis_title_offset = max([y_axis_title_offset, DOJO_Y_AXIS_TITLE_OFFSET])
    return y_axis_title_offset

def get_dojo_format_x_axis_numbers_and_labels(x_axis_categories: Sequence[Any]) -> str:
    """
    Dojo charts need string [{value: 1, text: "NZ"}, ...] as input to addAxis

    Args:
        x_axis_categories: e.g. ['NZ', 'Denmark', ...]
    """
    number_and_labels = []
    for n, category in enumerate(x_axis_categories, 1):
        number_and_labels.append(f'{{value: {n}, text: "{category}"}}')
    dojo_format_x_axis_numbers_and_labels = '[' + ',\n            '.join(number_and_labels) + ']'
    return dojo_format_x_axis_numbers_and_labels
