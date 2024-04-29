import unittest

import pandas as pd
from emec_2021.emec import create_catalog, EmecField
from emec_2021.fdsn import to_text, to_xml


class TestFdsn(unittest.TestCase):

    catalog = create_catalog()

    def test_catalog(self):
        assert pd.isna(self.catalog[EmecField.depth]).any()
        assert pd.isna(self.catalog[EmecField.mag]).any()
        cols = [c for c in self.catalog.columns if c not in
                (EmecField.depth, EmecField.mag)]
        assert pd.notna(self.catalog[cols]).all().all()

    def test_to_text(self):
        s = to_text(self.catalog.iloc[:1]).getvalue().decode('utf8')
        asd = 9
        # self.assertEqual(True, False)  # add assertion here

    def test_to_xml(self):
        cat = self.catalog[self.catalog[EmecField.iscid] > 0]
        s = to_xml(cat.iloc[:1]).getvalue().decode('utf8')
        asd = 9
        with open('/Users/rizac/work/gfz/projects/sources/python/emec_2021_restful_api/example.xml', 'wt') as _:
            _.write(s)
        # self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
