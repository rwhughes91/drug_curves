import pandas as pd
from pricerx import models
from calendar import monthrange


def multi_index_column_rename(columns):
    """
    This function was created for importing in BB data.
    The idea is to preserve the shape of the columns being imported; however, the nans are converted to
    'DATE'. The 'DATE' columns will later be dropped.
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
    """
    Used to query the desired drug data from the database. Returns a pandas df
    :param drugs:
    :return: pd.DataFrame
    """
    # Testing parameter is type: list
    if type(drugs) != list:
        raise TypeError("drugs must be type: list")

    # Connecting to the database
    with models.db:
        # Writing the query
        query = '''SELECT * FROM drug WHERE '''
        for index, drug in enumerate(drugs):
            if index == len(drugs) - 1:
                query += '''name = "{0}"'''.format(drug)
            else:
                query += '''name = "{0}" OR '''.format(drug)

        # Querying the results
        drugs_objects = list(models.Drug.raw(query))
        data_to_be_added = []
        for drug in drugs_objects:
            for strain in drug.strains:
                for price in strain.prices:
                    data_to_be_added.append(
                        [drug.name, drug.manufacturer, strain.strength, strain.package,
                         strain.form, price.date, price.price]
                    )
        # Organizing data into a pandas df
        columns = ["Drug", "Manufacturer", "Strength", "Package", "Form", "Effective Date", "Price"]
        pricerx_df = pd.DataFrame(data_to_be_added, columns=columns)

    return pricerx_df


def round_pricerx_prices(pricerx_df):
    """
    Takes in a specific dataframe (returned by pricerx_data_fetching) and rounds the effective dates.
    :param pricerx_df:
    :return: pd.DataFrame
    """
    # validating the input data
    if type(pricerx_df) != pd.DataFrame:
        raise TypeError("Needs to be a pd.DataFrame")
    elif list(pricerx_df.columns) != ["Drug", "Manufacturer", "Strength", "Package", "Form", "Effective Date", "Price"]:
        raise ValueError("this function is meant to be chained with pricerx_data_fetching function")

    # Rounded the dates
    def round_date(date):
        if date.day < 15:
            last_day_in_month = monthrange(month=date.month, year=date.year)[1]
            return pd.Timestamp(year=date.year, month=date.month, day=last_day_in_month)
        else:
            month = date.month + 1
            last_day_in_month = monthrange(month=month, year=date.year)[1]
            return pd.Timestamp(year=date.year, month=month, day=last_day_in_month)

    pricerx_df["Rounded Date"] = pricerx_df["Effective Date"].map(round_date)
    return pricerx_df


def expand_rounded_pricerx_prices(pricerx_df):
    """
    Takes in the returned dataframe from round_pricerx_prices
    the functionality is similar to pd.date_range, but also captures current prices
    this function will allow you to validate the data with a simple merge, easily pulling in the correct price
    :param pricerx_df:
    :return:
    """
    if type(pricerx_df) != pd.DataFrame:
        raise TypeError("Needs to be a pd.DataFrame")
    elif list(pricerx_df.columns) != ["Drug", "Manufacturer", "Strength", "Package", "Form", "Effective Date",
                                      "Price", "Rounded Date"]:
        raise ValueError("this function is meant to be chained with the round_pricerx_prices function")

    # grouping the data by 'uniqueness'
    list_of_unique_df_groups = []
    groups = pricerx_df.groupby(["Drug", "Manufacturer", "Strength", "Package", "Form"])
    for (name, manufacturer, strength, package, form), unique_frame in groups:
        list_of_unique_df_groups.append(unique_frame)

    # expanding the frame
    def expand_frame(frame):
        # validating the grouping
        columns_to_pull_for_test = ["Drug", "Manufacturer", "Strength", "Package", "Form"]
        if frame.loc[:, columns_to_pull_for_test].nunique().sum() != len(columns_to_pull_for_test):
            raise ValueError("Non unique groups need to be passed to this function")

        frame = frame.sort_values(by="Rounded Date").reset_index(drop=True)
        expanded_df = pd.DataFrame()

        for index in range(frame.shape[0]):
            current_round = frame.loc[index, "Rounded Date"]
            current_price = frame.loc[index, "Price"]

            if index == frame.shape[0] - 1:
                today = pd.Timestamp('today')
                last_day_in_current_month = monthrange(year=today.year, month=today.month)[1]
                next_round = pd.Timestamp(year=today.year, month=today.month, day=last_day_in_current_month)
                date_range = pd.date_range(current_round, next_round, freq="M")
            else:
                next_round = frame.loc[(index+1), "Rounded Date"]
                date_range = pd.date_range(current_round, next_round, freq="M", closed="left")

            expanded_df = expanded_df.append(pd.DataFrame(current_price, index=date_range, columns=["Price"]))

        # given the grouping, any i will pull the same value so i went with 0
        expanded_df["Drug"] = frame.loc[0, "Drug"]
        expanded_df["Manufacturer"] = frame.loc[0, "Manufacturer"]
        expanded_df["Strength"] = frame.loc[0, "Strength"]
        expanded_df["Package"] = frame.loc[0, "Package"]
        expanded_df["Form"] = frame.loc[0, "Form"]

        return expanded_df

    # appending the groups on one another
    expanded_frame = pd.DataFrame()
    for frame in list_of_unique_df_groups:
        expanded_frame = expanded_frame.append(expand_frame(frame))

    expanded_frame.index.name = "Rounded Date"

    return expanded_frame


if __name__ == "__main__":
    drugs = ["Levophed Bitartrate", "Norepinephrine Bitartrate"]
    df = pricerx_data_fetching(drugs)
    df = round_pricerx_prices(df)
    df_expanded = expand_rounded_pricerx_prices(df)
