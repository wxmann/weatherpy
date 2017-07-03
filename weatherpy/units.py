import math

import numpy as np


def get(unit_abbrev):
    try:
        x = float(unit_abbrev)
        return Scale(x1=x)
    except ValueError:
        return _units_repo[unit_abbrev]


class Unit(object):
    def __init__(self, name, dim, abbrevs, repo):
        self._name = name
        self._dim = dim
        if abbrevs:
            self._abbrevs = tuple(abbrevs)
        else:
            self._abbrevs = (self._name,)
        self._repo = repo

        self._repo.register_unit(self, self._abbrevs)

    @property
    def name(self):
        return self._name

    @property
    def dimension(self):
        return self._dim

    @property
    def abbrevs(self):
        return self._abbrevs

    def convert(self, val, from_unit):
        if from_unit == self:
            return val
        if self._repo is None:
            raise UnitsException("Unexpected error: repo not initialized")
        if from_unit.dimension != self.dimension:
            raise ValueError("Cannot convert from a unit of different dimension: " + str(from_unit))
        return self._repo.convert(val, from_unit, self)

    def __str__(self):
        return 'Unit(name={name}, dimension={dim})'.format(name=self.name, dim=self.dimension)

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, Unit) and (self.name, self.dimension) == (other.name, other.dimension)

    def __hash__(self):
        return hash((self.name, self.dimension))


class Scale(object):
    def __init__(self, x0=0.0, x1=1.0):
        if x0 == x1:
            raise ValueError("Lower and upper bounds of scale cannot be same")
        self._x0 = x0
        self._x1 = x1

    @property
    def bounds(self):
        return self._x0, self._x1

    @property
    def abbrevs(self):
        return '{}-{}'.format(self._x0, self._x1),

    @property
    def dimension(self):
        return None

    def convert(self, val, original_scale):
        if not isinstance(original_scale, Scale):
            raise UnitsException("Cannot convert to a unit that is not a scale")
        original_x0, original_x1 = original_scale.bounds

        # TODO: first half of this expression is encapsulate by internal.relative_percentage function,
        # but we've hit some import hell/circular dependency problems. We might want to fix this.
        return (val - original_x0) / (original_x1 - original_x0) * (self._x1 - self._x0) + self._x0

    def reverse(self):
        return Scale(self._x1, self._x0)

    def __str__(self):
        return 'ScaleUnit(min={}, max={})'.format(self._x0, self._x1)

    def __eq__(self, other):
        if self is other:
            return True
        return isinstance(other, Scale) and other.bounds == self.bounds

    def __hash__(self):
        return hash(self.bounds)


class UnitsRepository(object):
    def __init__(self):
        self._units = {}
        self._conversions = {}

    def register_unit(self, unit, abbrs):
        for abbr in abbrs:
            self._units[abbr.lower()] = unit
        self._units[unit.name.lower()] = unit

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

KELVIN = Unit('Kelvin', 'Temperature', ('K',), _units_repo)
CELSIUS = Unit('Celsius', 'Temperature', ('C', '°C'), _units_repo)
DBZ = Unit('dBz', 'Reflectivity', ('dBz',), _units_repo)
KNOT = Unit('Knot', 'Speed', ('kt', 'knots', 'kts'), _units_repo)
METER_PER_SECOND = Unit('Meter per Second', 'Speed', ('m/s', 'ms-1', 'mps', 'meters per second'),
                        _units_repo)
MILE = Unit('Mile', 'Length', ('mi',), _units_repo)
KILOMETER = Unit('Kilometer', 'Length', ('km',), _units_repo)
DEGREE = Unit('Degree', 'Angle', ('deg', '°'), _units_repo)
RADIAN = Unit('Radian', 'Angle', ('rad',), _units_repo)

_units_repo.register_conversion(KELVIN, CELSIUS, lambda k: k - 273.15)
_units_repo.register_conversion(CELSIUS, KELVIN, lambda c: c + 273.15)
_units_repo.register_conversion(METER_PER_SECOND, KNOT, lambda ms: ms * 1.944)
_units_repo.register_conversion(KNOT, METER_PER_SECOND, lambda kt: kt / 1.944)
_units_repo.register_conversion(MILE, KILOMETER, lambda mi: mi * 1.60934)
_units_repo.register_conversion(KILOMETER, MILE, lambda km: km / 1.60934)
_units_repo.register_conversion(DEGREE, RADIAN, math.radians)
_units_repo.register_conversion(RADIAN, DEGREE, math.degrees)


def arrayconvert(unit1, unit2):
    def convert(x):
        return unit1.convert(x, unit2)

    return np.vectorize(convert)