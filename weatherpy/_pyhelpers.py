def coalesce_kwargs(kwargs, **fallback_values):
    result = {k: v for k, v in kwargs.items()}
    for fallback_k in fallback_values:
        if fallback_k not in result:
            result[fallback_k] = fallback_values[fallback_k]
    return result