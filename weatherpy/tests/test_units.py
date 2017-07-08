import unittest
from unittest import mock

from weatherpy import units
from weatherpy.units import UnitsException, Scale


class Test_Units(unittest.TestCase):
    def setUp(self):
        self.dummy_repo = mock.MagicMock()
        self.dummy_repo.register_unit = mock.MagicMock()

    def test_should_get_kelvin_unit(self):
        self._assert_can_get_unit(('K', 'Kelvin'), units.KELVIN)

    def test_should_get_celsius_unit(self):
        self._assert_can_get_unit(('C', '°C', 'Celsius'), units.CELSIUS)

    def test_should_get_dbz_unit(self):
        self._assert_can_get_unit(('dbz',), units.DBZ)

    def test_should_get_knots_unit(self):
        self._assert_can_get_unit(('kt', 'knot', 'knots', 'kts'), units.KNOT)

    def test_should_get_mps_unit(self):
        self._assert_can_get_unit(('mps', 'ms-1', 'm/s', 'meters per second', 'meter per second'),
                                  units.METER_PER_SECOND)

    def test_should_get_mi_unit(self):
        self._assert_can_get_unit(('mi', 'mile'), units.MILE)

    def test_should_get_km_unit(self):
        self._assert_can_get_unit(('km', 'kilometer'), units.KILOMETER)

    def test_should_get_m_unit(self):
        self._assert_can_get_unit(('m', 'meter'), units.METER)

    def test_should_get_deg_unit(self):
        self._assert_can_get_unit(('deg', '°'), units.DEGREE)

    def test_should_get_rad_unit(self):
        self._assert_can_get_unit(('rad',), units.RADIAN)

    def test_should_get_scale_unit(self):
        unit = units.get('256')
        self.assertEqual(unit, units.Scale(0, 256))

    def test_should_not_get_invalid_unit(self):
        with self.assertRaises(UnitsException):
            units.get('what')

    def test_unit_equality(self):
        unit1 = units.Unit('kt', 'speed', abbrevs=(), repo=self.dummy_repo)
        unit2 = units.Unit('kt', 'speed', abbrevs=('kts',), repo=self.dummy_repo)
        unit3 = units.Unit('mps', 'speed', abbrevs=('kts',), repo=self.dummy_repo)

        self.assertEqual(unit1, unit2)
        self.assertNotEqual(unit1, unit3)
        self.assertNotEqual(unit2, unit3)

    def test_should_register_with_repo(self):
        unit = units.Unit('dummy_unit', 'speed', abbrevs=(), repo=self.dummy_repo)
        self.dummy_repo.register_unit.assert_called_with(unit, ('dummy_unit',))

    def _assert_can_get_unit(self, abbrs, unit):
        for abr in abbrs:
            self.assertEqual(units.get(abr), unit,
                             msg='Unit: {} does not match expected: {}'.format(str(units.get(abr)),
                                                                               str(unit)))


class Test_UnitsConversion(unittest.TestCase):
    def test_convert_C_to_K(self):
        deg_C = 30
        deg_K = units.KELVIN.convert(deg_C, units.CELSIUS)
        self.assertAlmostEqual(deg_K, 303.15)

    def test_convert_K_to_C(self):
        deg_K = 303.15
        deg_C = units.CELSIUS.convert(deg_K, units.KELVIN)
        self.assertAlmostEqual(deg_C, 30)

    def test_convert_to_same_unit(self):
        deg_K = 303.15
        deg_K_2 = units.KELVIN.convert(deg_K, units.KELVIN)
        self.assertAlmostEqual(deg_K, deg_K_2)

    def test_convert_kt_to_mps(self):
        speed_kt = 50
        speed_mps = units.METER_PER_SECOND.convert(speed_kt, units.KNOT)
        self.assertAlmostEqual(speed_mps, 25.72, 2)

    def test_convert_mps_to_kt(self):
        speed_mps = 25.72
        speed_kt = units.KNOT.convert(speed_mps, units.METER_PER_SECOND)
        self.assertAlmostEqual(speed_kt, 50.00, 2)

    def test_convert_mi_to_km(self):
        self.assertAlmostEqual(units.KILOMETER.convert(15, units.MILE), 24.1402, 3)

    def test_convert_km_to_mi(self):
        self.assertAlmostEqual(units.MILE.convert(24.1402, units.KILOMETER), 15, 3)

    def test_convert_km_to_m(self):
        self.assertAlmostEqual(units.METER.convert(1, units.KILOMETER), 1000)

    def test_convert_m_to_km(self):
        self.assertAlmostEqual(units.KILOMETER.convert(1000, units.METER), 1)

    def test_convert_mi_to_m(self):
        self.assertAlmostEqual(units.METER.convert(1, units.MILE), 1609.34, 2)

    def test_convert_m_to_mi(self):
        self.assertAlmostEqual(units.MILE.convert(1609.34, units.METER), 1, 2)


class Test_Scale(unittest.TestCase):
    def test_scale_conversion(self):
        q1 = 0.2
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 60)

        q2 = scale2.convert(q1, scale1)
        self.assertAlmostEqual(q2, 20)

    def test_scale_reversal(self):
        scale = Scale(5, 55.5)
        reversed = scale.reverse()
        self.assertEqual(reversed.bounds, (55.5, 5))

    def test_scale_reversal_and_conversion(self):
        q1 = 0.2
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 60).reverse()

        q2 = scale2.convert(q1, scale1)
        self.assertAlmostEqual(q2, 50)

    def test_scale_conversion_out_of_bounds(self):
        q1 = 1.5
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 50)
        scale3 = scale2.reverse()

        q2 = scale2.convert(q1, scale1)
        self.assertAlmostEqual(q2, 70)

        q3 = scale3.convert(q1, scale1)
        self.assertAlmostEqual(q3, -10)

    def test_scale_should_not_be_created_with_same_upper_lower_bound(self):
        with self.assertRaises(ValueError):
            Scale(1, 1)

    def test_scale_abbreviations_are_just_bound(self):
        s = Scale(1, 5)
        self.assertEqual(s.abbrevs, ('1-5',))

    def test_scale_eq(self):
        self.assertEqual(Scale(2, 5.5), Scale(2, 6.5 - 1))
        self.assertNotEqual(Scale(2, 5.5), Scale(1.5, 3.75))
