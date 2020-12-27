import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')


__all__ = [
    'validate_numeric',
]


def validate_numeric(value: str,
                     default,
                     min_val,
                     max_val,
                     is_float=False):
    """ Validate numeric variable (for API parameter validation)

     Parameter
    ---------------
    value: str
        string value
    default: numeric
        default value if given value is None or ""
    min_val: numeric
        numeric value for minimum value
    max_val: numeric
        numeric value for maximum value
    is_float: bool
        use `float` if True else `int`

     Return
    ---------------
    flag: bool
        error flag True if there's any error
    value:
        value for the parameter
    """
    if value == '' or value is None:
        value = default
    try:
        if is_float:
            value = float(value)
        else:
            value = int(value)
    except ValueError:
        return False, f'Param must be a numeric value between "{min_val}" and "{max_val}"'

    if type(max_val) is not float and type(max_val) is not int:
        return False, 'max_val is not numeric: %s' % str(max_val)

    if type(min_val) is not float and type(min_val) is not int:
        return False, 'min_val is not numeric: %s' % str(min_val)

    if value > max_val or value < min_val:
        return False, f'Param must be between {min_val} and {max_val} but {value}'

    return True, value
