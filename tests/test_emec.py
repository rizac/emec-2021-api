import os
import shutil
import unittest
from contextlib import contextmanager
from os.path import dirname, join, isdir
from unittest.mock import patch

import pandas as pd
from emec_2021.emec import create_catalog, EmecField, SOURCE_FILENAME

DEST_PATH = join(dirname(__file__), 'tmp')

@contextmanager
def mock_open_source_catalog(*a, **kw):
    yield open(join(dirname(dirname(__file__)), 'emec_2021', SOURCE_FILENAME), 'rb')


class TestEmec(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not isdir(DEST_PATH):
            os.mkdir(DEST_PATH)

    @classmethod
    def tearDownClass(cls):
        if isdir(DEST_PATH):
            shutil.rmtree(DEST_PATH)

    @patch('emec_2021.emec.open_source_catalog', side_effect=mock_open_source_catalog)
    @patch('emec_2021.emec.DEST_PATH', DEST_PATH)
    def test_catalog(self, mock_open_source_catalog):
        catalog = create_catalog(force_reload=True, verbose=False)
        fields_with_na = {EmecField.depth, EmecField.mag}
        for col in catalog.columns:
            has_na = pd.isna(catalog[col]).any()
            assert has_na == (col in fields_with_na)


if __name__ == '__main__':
    unittest.main()
