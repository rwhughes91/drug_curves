import pandas as pd
from pricerx import models


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


def pricerx_data_fetching(drugs):
    # Testing parameter is type: list
    if type(drugs) != list:
        raise TypeError("drugs must be type: list")

    # Connecting to the database
    with models.db:
        # Writing the query
        query = '''SELECT * FROM drug WHERE'''
        for index, drug in enumerate(drugs):
            if index == len(drugs) - 1:
                query += '''name= "{0]"'''.format(drug)
            else:
                query += '''name={0} OR '''.format(drug)

        # Querying the results
        drugs_objects = list(models.Drug.raw(query))
        data_to_be_added = []
        for drug in drugs_objects:
            for strain in drug.strains:
                for price in strain.prices:
                    data_to_be_added.append(
                        [drug.name, strain.strength, strain.package,
                         strain.form, price.date, price.price]
                    )
        # Organizing data into a pandas df
        columns = ["Drug", "Strength", "Package", "Form", "Effective Date", "Price"]
        pricerx_df = pd.DataFrame(data_to_be_added, columns=columns)

    return pricerx_df
