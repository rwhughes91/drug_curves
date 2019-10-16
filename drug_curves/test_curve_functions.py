import unittest
import os
import pandas as pd

from drug_curves.curve_functions import multi_index_column_rename


file = "Norepinephrine Market vRH.xlsx"
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "imports", file))


class TestMultiIndexColumnRename(unittest.TestCase):
    def setUp(self):
        self.raw_data = pd.read_excel(path, sheet_name="BB New", header=[0, 1, 2])
        self.multi_index_columns = multi_index_column_rename(self.raw_data.columns)

    def test_import(self):
        assert type(self.raw_data) == pd.DataFrame
        assert type(self.multi_index_columns) == pd.MultiIndex


if __name__ == "__main__":
    unittest.main()
