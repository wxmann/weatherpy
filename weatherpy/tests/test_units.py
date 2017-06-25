import unittest

from weatherpy import units
from weatherpy.units import UnitsException, Scale


class Test_Units(unittest.TestCase):

    def test_should_get_kelvin_unit(self):
        unit_k = units.get('K')
        self.assertEqual(unit_k, units.KELVIN)

        unit_k_2 = units.get('Kelvin')
        self.assertEqual(unit_k_2, units.KELVIN)

    def test_should_get_celsius_unit(self):
        unit_c_1 = units.get('C')
        unit_c_2 = units.get('°C')
        unit_c_3 = units.get('Celsius')

        for unit in (unit_c_1, unit_c_2, unit_c_3):
            self.assertEqual(unit, units.CELSIUS)

    def test_should_get_dbz_unit(self):
        unit_dbz = units.get('dbZ')
        self.assertEqual(unit_dbz, units.DBZ)

    def test_should_get_knots_unit(self):
        unit_kt1 = units.get('kt')
        unit_kt2 = units.get('knot')
        unit_kt3 = units.get('knots')
        unit_kt4 = units.get('kts')

        for unit in (unit_kt1, unit_kt2, unit_kt3, unit_kt4):
            self.assertEqual(unit, units.KNOT)

    def test_should_get_mps_unit(self):
        unit_mps1 = units.get('mps')
        unit_mps2 = units.get('ms-1')
        unit_mps3 = units.get('m/s')
        unit_mps4 = units.get('meters per second')
        unit_mps5 = units.get('meter per second')

        for unit in unit_mps1, unit_mps2, unit_mps3, unit_mps4, unit_mps5:
            self.assertEqual(unit, units.METER_PER_SECOND)

    def test_should_get_scale_unit(self):
        unit = units.get('256')
        self.assertEqual(unit, units.Scale(0, 256))

    def test_should_not_get_invalid_unit(self):
        with self.assertRaises(UnitsException):
            units.get('what')


class Test_UnitsConversion(unittest.TestCase):

    def test_convert_C_to_K(self):
        deg_C = 30
        deg_K = units.CELSIUS.convert(deg_C, units.KELVIN)
        self.assertAlmostEqual(deg_K, 303.15)

    def test_convert_K_to_C(self):
        deg_K = 303.15
        deg_C = units.KELVIN.convert(deg_K, units.CELSIUS)
        self.assertAlmostEqual(deg_C, 30)

    def test_convert_to_same_unit(self):
        deg_K = 303.15
        deg_K_2 = units.KELVIN.convert(deg_K, units.KELVIN)
        self.assertAlmostEqual(deg_K, deg_K_2)

    def test_convert_kt_to_mps(self):
        speed_kt = 50
        speed_mps = units.KNOT.convert(speed_kt, units.METER_PER_SECOND)
        self.assertAlmostEqual(speed_mps, 25.72, 2)

    def test_convert_mps_to_kt(self):
        speed_mps = 25.72
        speed_kt = units.METER_PER_SECOND.convert(speed_mps, units.KNOT)
        self.assertAlmostEqual(speed_kt, 50.00, 2)


class Test_Scale(unittest.TestCase):

    def test_scale_conversion(self):
        q1 = 0.2
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 60)

        q2 = scale1.convert(q1, scale2)
        self.assertAlmostEqual(q2, 20)

    def test_scale_reversal(self):
        scale = Scale(5, 55.5)
        reversed = scale.reverse()
        self.assertEqual(reversed.bounds, (55.5, 5))

    def test_scale_reversal_and_conversion(self):
        q1 = 0.2
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 60).reverse()

        q2 = scale1.convert(q1, scale2)
        self.assertAlmostEqual(q2, 50)

    def test_scale_conversion_out_of_bounds(self):
        q1 = 1.5
        scale1 = Scale(0, 1)
        scale2 = Scale(10, 50)
        scale3 = scale2.reverse()

        q2 = scale1.convert(q1, scale2)
        self.assertAlmostEqual(q2, 70)

        q3 = scale1.convert(q1, scale3)
        self.assertAlmostEqual(q3, -10)

    def test_scale_should_not_be_created_with_same_upper_lower_bound(self):
        with self.assertRaises(ValueError):
            Scale(1, 1)

    def test_scale_abbreviations_are_just_bound(self):
        s = Scale(1, 5)
        self.assertEqual(s.abbrevs, ('1-5',))
