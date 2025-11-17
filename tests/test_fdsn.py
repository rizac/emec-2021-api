import unittest

import pandas as pd
import re
from emec_2021.emec import create_catalog, EmecField
from emec_2021.fdsn import to_text, to_xml


class TestFdsn(unittest.TestCase):

    catalog = create_catalog(force_reload=False, verbose=False)

    def test_to_text(self):
        ctl = self.catalog[self.catalog[EmecField.eventid] == 1900010867915]
        s = to_text(ctl).getvalue().decode('utf8')
        expected_mag = ctl[EmecField.mag].iloc[0]
        assert f"|Mw|{expected_mag}|" in s
        # self.assertEqual(True, False)  # add assertion here

    def test_to_xml(self):
        ctl = self.catalog[self.catalog[EmecField.eventid] == 1900010867915]
        s = to_xml(ctl).getvalue().decode('utf8')
        grps = re.findall(r"<mag>\s*<value>(.*?)</value>\s*</mag>", s)
        expected_mag = ctl[EmecField.mag].iloc[0]
        assert grps[0] == str(expected_mag) and grps[1] != grps[0]
        # self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
