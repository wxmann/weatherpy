from datetime import datetime


def coalesce_kwargs(kwargs, **fallback_values):
    result = {k: v for k, v in kwargs.items()}
    for fallback_k in fallback_values:
        if fallback_k not in result:
            result[fallback_k] = fallback_values[fallback_k]
    return result


# splitting this out for testing purposes.
def current_time_utc():
    return datetime.utcnow()


def index_time_slice_helper(func_if_int, func_if_time):
    def handle_slice_func(sliceobj):
        start = sliceobj.start
        stop = sliceobj.stop

        use_index = any([
            isinstance(start, int) or isinstance(stop, int),
            start is None and stop is None
        ])
        use_timestamp = isinstance(start, datetime) or isinstance(stop, datetime)
        invalid = any([
            use_index and use_timestamp,
            not isinstance(start, (int, datetime)) and start is not None,
            not isinstance(stop, (int, datetime)) and stop is not None
        ])
        if invalid:
            raise ValueError("Invalid slice, check your values")

        if use_index:
            return func_if_int(sliceobj)
        elif use_timestamp:
            return func_if_time(sliceobj)
        else:
            raise ValueError("Invalid slice, check your values")
    return handle_slice_func
