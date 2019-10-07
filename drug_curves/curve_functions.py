import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def multi_index_column_rename(columns):
    """
    This function was created for importing in BB data.
    The idea is to preserve the shape of the columns being imported; however, the nans are converted to
    'DATE'
    """
    if type(columns) != pd.MultiIndex:
        raise TypeError("This function is for pd.MultiIndex columns")
    else:
        num_of_levels = len(columns.levels)
        col = []
        for i in range(num_of_levels):
            # title the elements of the series
            frozen_series = pd.Series(columns.get_level_values(i)).str.title()
            if i != (num_of_levels - 1):
                col.append(list(frozen_series))
            else:
                col.append(list(frozen_series.fillna("Date")))
        return pd.MultiIndex.from_arrays(col)
