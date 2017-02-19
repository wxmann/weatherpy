import warnings


class Properties(dict):
    def __init__(self, **kwargs):
        super(Properties, self).__init__(kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            warnings.warn("Property: {} does not exist. Defaulting to None.")
            return None
