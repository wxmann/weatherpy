
KELVIN = 'temperature_Kelvin'

CELSIUS = 'temperature_Celsius'

DBZ = 'reflectivity_dBz'

KNOTS = 'speed_Knots'

METERS_PER_SECOND = 'speed_m/s'


def get(unit_repr):
    return _units_repo[unit_repr]


def convert(val, from_unit, to_unit):
    return _units_repo.convert(val, from_unit, to_unit)


class UnitsRepository(object):
    def __init__(self):
        self._units = {}
        self._conversions = {}

    def register_unit(self, unit, abbrs):
        for abbr in abbrs:
            self._units[abbr.lower()] = unit

    def register_conversion(self, from_unit, to_unit, func):
        if from_unit not in self._conversions:
            self._conversions[from_unit] = {}
        self._conversions[from_unit][to_unit] = func

    def convert(self, val, from_unit, to_unit):
        try:
            return self._conversions[from_unit][to_unit](val)
        except KeyError:
            raise UnitsException("Conversion from {} to {} not registered".format(from_unit, to_unit))

    def __getitem__(self, item):
        try:
            return self._units[item.lower()]
        except KeyError:
            raise UnitsException("Invalid unit: " + str(item))


class UnitsException(Exception):
    pass


_units_repo = UnitsRepository()

_units_repo.register_unit(KELVIN, ('K', 'Kelvin'))
_units_repo.register_unit(CELSIUS, ('C', '°C', 'Celsius'))
_units_repo.register_unit(DBZ, ('dBz',))
_units_repo.register_unit(KNOTS, ('kt', 'knots'))
_units_repo.register_unit(METERS_PER_SECOND, ('m/s', 'meters per second', 'ms-1', 'mps'))

_units_repo.register_conversion(KELVIN, CELSIUS, lambda k: k - 273.15)
_units_repo.register_conversion(CELSIUS, KELVIN, lambda c: c + 273.15)
_units_repo.register_conversion(METERS_PER_SECOND, KNOTS, lambda ms: ms * 1.944)
_units_repo.register_conversion(KNOTS, METERS_PER_SECOND, lambda kt: kt / 1.944)


