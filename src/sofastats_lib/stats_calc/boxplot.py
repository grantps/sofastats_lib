
def get_bottom_whisker(raw_bottom_whisker, box_bottom, vals):
    """
    Make no lower than the minimum value within (inclusive) 1.5*iqr below lq.
    Must never go above box_bottom.
    """
    bottom_whisker = raw_bottom_whisker  ## init
    for val in sorted(vals):  ## going upwards
        if val < raw_bottom_whisker:
            pass  ## keep going up
        elif val >= raw_bottom_whisker:
            bottom_whisker = val
            break
    if bottom_whisker > box_bottom:
        bottom_whisker = box_bottom
    return bottom_whisker

def get_top_whisker(raw_top_whisker, box_top, vals):
    """
    Make sure no higher than the maximum value within (inclusive)
    1.5*iqr above uq. Must never fall below ubox.
    """
    top_whisker = raw_top_whisker  ## init
    for val in reversed(vals):  ## going downwards
        if val > raw_top_whisker:
            pass  ## keep going down
        elif val <= raw_top_whisker:
            top_whisker = val
            break
    if top_whisker < box_top:
        top_whisker = box_top
    return top_whisker
