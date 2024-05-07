import unittest

import pandas as pd
from emec_2021.emec import create_catalog, EmecField
from emec_2021.fdsn import to_text, to_xml


class TestFdsn(unittest.TestCase):

    catalog = create_catalog(force_reload=False, verbose=False)

    def test_to_text(self):
        s = to_text(self.catalog.iloc[:1]).getvalue().decode('utf8')
        asd = 9
        # self.assertEqual(True, False)  # add assertion here

    def test_to_xml(self):
        s = to_xml(self.catalog.iloc[:1]).getvalue().decode('utf8')
        # self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
