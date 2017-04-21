import unittest

from weatherpy.internal.pyhelpers import coalesce_kwargs


class PyHelpersTests(unittest.TestCase):

    def test_should_use_kwargs_over_fallbacks(self):
        kwargs = {'a': 1, 'b': 2}
        fallbacks = {'a': 11 , 'b': 22}
        self.assertDictEqual(coalesce_kwargs(kwargs, **fallbacks), kwargs)

    def test_should_use_all_fallbacks_if_kwargs_empty(self):
        kwargs = {}
        fallbacks = {'a': 11, 'b': 22}
        self.assertDictEqual(coalesce_kwargs(kwargs, **fallbacks), fallbacks)

    def test_should_use_mix_of_kwargs_and_fallbacks(self):
        kwargs = {'a': 1, 'b': 2}
        fallbacks = {'b': 22, 'c': 33, 'd': 44}
        self.assertDictEqual(coalesce_kwargs(kwargs, **fallbacks), {
            'a': 1,
            'b': 2,
            'c': 33,
            'd': 44
        })