from unittest import TestCase
from unittest.mock import patch, call

from weatherpy.ctables.repos import Repo


class TestRepo(TestCase):
    @patch('weatherpy.ctables.repos.load_colortable')
    def test_should_add_pal_to_repo(self, load_ctable_func):
        repo = Repo()
        repo.test = 'test.pal'
        load_ctable_func.assert_not_called()

        repo.test
        args = load_ctable_func.call_args[0]
        self.assertEqual(args[0], 'test')
        self.assertTrue(args[1].endswith('test.pal'))

    def test_should_add_mpl_cmap_to_repo(self):
        repo = Repo()
        repo.test = 'cmap'

        x = repo.test
        self.assertEqual(x, 'cmap')