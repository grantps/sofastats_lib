from dataclasses import dataclass
from enum import StrEnum
from typing import Any

@dataclass(frozen=True, kw_only=True)
class ValSpec:
    """
    Data as taken from data source in data extraction context. Not about output of any sort at this stage.
    """
    val: Any
    lbl: str

@dataclass(frozen=True)
class ValFilterSpec:
    """
    E.g. for filtering a dataset to get a sample.
    """
    variable_name: str
    val_spec: ValSpec
    val_is_numeric: bool

class ValType(StrEnum):
    """
    Value type - relevant to database engines, validation etc.
    """
    IS_SEQ = 'is_sequence'
    IS_NULLABLE = 'is_nullable'
    DATA_ENTRY_OK = 'data_entry_ok'  ## e.g. not autonumber, timestamp etc
    IS_DEFAULT = 'is_default'
    ## test
    TEXT = 'is_text'
    TEXT_LENGTH = 'text_length'
    CHARSET = 'charset'
    ## numbers
    IS_NUMERIC = 'is_numeric'
    IS_AUTONUMBER = 'is_autonumber'
    DECIMAL_PTS = 'decimal_points'
    NUM_WIDTH = 'numeric_display_width'  ## used for column display only
    IS_NUM_SIGNED = 'is_numeric_signed'
    NUM_MIN_VAL = 'numeric_minimum_value'
    NUM_MAX_VAL = 'numeric_maximum_value'
    ## datetime
    IS_DATETIME = 'is_datetime'
