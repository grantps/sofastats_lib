import datetime

def get_dt_from_datetime_str(datetime_str: str) -> datetime.datetime:
    """
    Only expecting and accepting standardised dates / times.
    Up to function passing dates in to preprocess into this form
    if not already suitable.
    """
    acceptable_formats = [
        '%Y-%m-%d %I:%M:%S',
        '%Y-%m-%d',
        '%Y-%m',
        '%Y',
        '%I:%M:%S',
    ]
    dt = None
    for acceptable_format in acceptable_formats:
        try:
            dt = datetime.datetime.strptime(datetime_str, acceptable_format)
            return dt
        except ValueError:
            continue
    if dt is None:
        acceptable_formats_str = "'" + "', '".join(acceptable_formats) + "'"
        raise ValueError(f"Inappropriate date/time format received - '{datetime_str}'"
            f"\nAcceptable formats are {acceptable_formats_str}")

def get_epoch_secs_from_datetime_str(datetime_str: str) -> int:
    """
    Takes a string and checks if there is a usable datetime in there.
    A time without a date is OK. As is a yrmonth or year only.

    If there is a usable datetime, returns seconds since epoch (1970).
    Can be a negative value.
    """
    dt = get_dt_from_datetime_str(datetime_str)
    epoch_start_dt = datetime.datetime(1970, 1, 1)
    epoch_seconds = (dt - epoch_start_dt).total_seconds()
    return epoch_seconds
