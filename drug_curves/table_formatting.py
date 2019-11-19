import os
import pandas as pd
import numpy as np

from calendar import month_name
from datetime import date, timedelta

from .curve_functions import rns_data_fetching

templates = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
template = os.path.join(templates, "tables_template.html")
css = os.path.join(templates, 'css', 'table_styles.css')

with open(template, "r") as f:
    base_html = f.read()


def percentage_formatter(val):
    val = "{:.0%}".format(val)
    if val == "nan%":
        return ""
    elif val == "99999999%":
        return "N/A"
    else:
        return val


def volume_formatter(val):
    val = f"{val:,}"
    if val == "nan":
        return ""
    else:
        return val.replace(".0", "")


def wac_formatter(val):
    if val == "Does not break out U.S. Sales":
        return val
    else:
        val = f"{val:,}"
        if val == "nan":
            return "N/A"
        else:
            return "$" + val.replace(".0", "")


class Report:
    def __init__(self, calculated_df, title):
        self.counter = {
            "VolumeTables": {
                "count": 0,
                "table_html": [],
            },
            "PriceTables": {
                "count": 0,
                "table_html": [],
            },
            "WacTables": {
                "count": 0,
                "table_html": [],
            },
        }
        self.graphs = {
            "VolumeGraph": 'volume.png',
            "PriceGraph": 'price.png',
            "WacGraph": 'wac.png',
        }
        self.full_report = base_html.replace("(% Title %)", title)

        self.calculated_df = calculated_df.copy()
        self.title = title
        self.last_three_months = self.calculated_df.index.unique().sort_values(ascending=False)[:3]
        self.last_month = self.last_three_months[0]

        self.calculated_df["Pres Name"] = self.calculated_df["Drug"].str.split(" ").str[0] \
                                          + " (" + self.calculated_df["Manufacturer"] + ")"
        self.rns_df = rns_data_fetching(list(self.calculated_df["Drug"].str.split().str[0].unique()))
        self.ttm_date = self.generate_ttm_date()

    def generate_ttm_date(self):
        d = date(year=1991, month=12, day=18)
        for name, group in self.rns_df.groupby("Drug"):
            if group["Date"].max() > d:
                d = group["Date"].max()
        return d

    def generate_ttm_df(self, title, how="wac"):
        if how == "wac":
            last_month_reported = pd.Timestamp(self.ttm_date)
            last_month_cutoff = last_month_reported - timedelta(days=365)
        else:
            last_month_reported = self.calculated_df.index.max()
            last_month_cutoff = last_month_reported - timedelta(days=365)
        ttm_df = self.calculated_df.loc[(self.calculated_df.index <= last_month_reported) &
                                        (self.calculated_df.index > last_month_cutoff), :].copy()
        ttm_df = ttm_df.pivot_table(index="Pres Name", values=title, aggfunc="sum")
        return ttm_df.sort_values(title, ascending=False).copy()

    def generate_net_to_wac(self, title):
        # Grabbing the TTM WAC
        ttm_df = self.generate_ttm_df(title)
        ttm_df["Label"] = ttm_df.index.str.split().str[0]
        ttm_df = ttm_df.reset_index().set_index("Label")
        # Grabbing the TTM RNS
        rns_df_pivoted = pd.DataFrame()
        for name, group in self.rns_df.groupby("Drug"):
            last_four = group.sort_values("Date", ascending=False).iloc[0:4]
            last_four_by_drug = last_four.pivot_table(index="Drug", values="Reported Net Sales", aggfunc="sum")
            last_four_by_drug["Last_date"] = last_four["Date"].iloc[0]
            rns_df_pivoted = rns_df_pivoted.append(last_four_by_drug)
        # Setting the RNS to ttm_df and calculating net/wac
        ttm_df["RNS"] = rns_df_pivoted["Reported Net Sales"].astype(float)
        ttm_df = ttm_df.set_index("Pres Name")  # Re-Assigning the correct index
        ttm_df["Net/WAC"] = ttm_df["RNS"] / ttm_df["WAC"]
        return ttm_df

    def update_report(self, to_update, html):
        self.counter[to_update]["count"] += 1
        self.counter[to_update]["table_html"].append(html)

    def add_graphs(self, graphs):
        for key, chart in graphs.items():
            escape_char = "(% {} %)".format(key)
            image_tag = '\n    <img src="{}">'.format(chart)
            self.full_report = self.full_report.replace(escape_char, image_tag)

    def generate_report(self, weasyprint=False):
        if weasyprint:
            l = '<link rel = "stylesheet" href = "../../templates/css/wp_styles.css">'
        else:
            l = '<link rel = "stylesheet" href = "../../templates/css/table_styles.css">'
        self.full_report = self.full_report.replace("(% print %)", l)
        for key, values in self.counter.items():
            if values["count"] > 0:
                table_html = ""
                for table in values["table_html"]:
                    if values["table_html"].index(table) == len(values["table_html"])-1:
                        table_html += table
                    else:
                        table_html += table + "\n"
            else:
                table_html = ""
            escape_char = "(% {} %)".format(key)
            self.full_report = self.full_report.replace(escape_char, table_html)
        self.add_graphs(self.graphs)
        return self.full_report

    def three_month_volume_report(self, volume_units_name, title, convert_to_html=True):
        # Slicing the data
        volume_last_three_mo = self.calculated_df.loc[self.last_three_months, :].reset_index()
        # Pivoting for report
        vol_report = volume_last_three_mo.pivot_table(index="Pres Name", columns="Date", values=volume_units_name)
        # Sorting by most recent column
        vol_report = vol_report.sort_values(self.last_month, ascending=False)
        vol_report.index.name = "Drug"
        # Changing column names
        vol_report.columns = ["(" + name.strftime("%m/%d/%Y") + ")" for name in vol_report.columns]
        # Adding a bottom 'Total' Row
        vol_report.loc["Total"] = vol_report.sum()
        vol_report = vol_report.round()
        # Changing thee values for formatted strings
        if convert_to_html:
            vol_report = vol_report.applymap(volume_formatter)
        # Pushing index out for df.to_html(index=False)
        vol_report.reset_index(inplace=True)
        if convert_to_html:
            html = self.three_month_volume_summary_html(title, vol_report, vol_report.columns[1:])
            self.update_report("VolumeTables", html)
            return html
        else:
            return vol_report

    def annualized_report(self, vol_or_wac, unit_name, volume_column_name="Vials", n=1, convert_to_html=True,
                          wide=False, est_sales=False):
        months = self.calculated_df.index.unique().sort_values(ascending=False)[:n]
        last_month_data = self.calculated_df.loc[months, :].reset_index()
        # Determining if this is a volume or wac report
        if vol_or_wac.lower().startswith("v"):
            col_c = volume_column_name
            to_update = "VolumeTables"
            form = volume_formatter
        elif vol_or_wac.lower().startswith("w"):
            col_c = "WAC Sales"
            to_update = "WacTables"
            form = wac_formatter
        else:
            raise ValueError("vol_or_wac needs to be either vol | wac")
        # Dynamically creating the appropriate column names
        col_name = "Annualized {}".format(col_c)
        per_col_name = "% of {}".format(col_c)
        # Annual-izing the data
        annualized_data = last_month_data.pivot_table(index="Pres Name", values=unit_name,
                                                      aggfunc=lambda ser: (ser.sum() / ser.shape[0]) * 12)
        annualized_data.columns = [col_name]
        annualized_data[col_name] = annualized_data[col_name].round()  # rounding for WAC/Volume
        # Dropping and non producing rows
        annualized_data = annualized_data.loc[annualized_data[col_name] > 0, :].copy()  # to suppress warnings
        # Sorting
        annualized_data = annualized_data.sort_values(col_name, ascending=False)
        annualized_data.index.name = "Drug"
        # Creating percentages
        annualized_data[per_col_name] = annualized_data.apply(lambda col: col / col.sum()).round(2)
        # Appending a total row to the bottom
        annualized_data.loc["Total"] = annualized_data.sum()
        annualized_data.loc["Total", per_col_name] = 1.00
        # Adding the est. Annualized Net Sales
        title_col = "Est. Annualized Net Sales"
        if est_sales:
            n_to_wac_df = self.generate_net_to_wac(unit_name)
            annualized_data[title_col] = (annualized_data[col_name] * n_to_wac_df["Net/WAC"]).round()
            # Adding the Total Amount for the column
            annualized_data.loc["Total", title_col] = annualized_data[title_col].sum()
            # Changing NANs to "N/A"

        # Formatting the data into strings
        if convert_to_html:
            annualized_for_data = pd.DataFrame(annualized_data[col_name].apply(form))
            annualized_for_data[per_col_name] = annualized_data[per_col_name].apply(percentage_formatter)
            if est_sales:
                annualized_for_data[title_col] = annualized_data[title_col].apply(wac_formatter)
        else:
            annualized_for_data = pd.DataFrame(annualized_data[col_name])
            annualized_for_data[per_col_name] = annualized_data[per_col_name]
            if est_sales:
                annualized_for_data[title_col] = annualized_data[title_col]
        annualized_for_data.reset_index(inplace=True)

        if convert_to_html:
            classes = "report"
            if wide:
                classes += " wide"
            html = annualized_for_data.to_html(index=False).replace("dataframe", classes)
            str_add_on = '<br> <span class="small">(Based on Trailing {} Month</span>'.format(n)
            if n > 1:
                str_add_on += "s"
            str_add_on += ")"
            html = html.replace(col_name, col_name + str_add_on)
            if vol_or_wac.lower().startswith("w"):
                html = html.replace("$", '<span style="float: left;">$</span>')
            self.update_report(to_update, html)
            return html
        else:
            return annualized_for_data

    def ttm_report(self, vol_or_wac, unit_name, volume_column_name="Vials", convert_to_html=True, wide=False):
        # Determining if this is a volume or wac report
        if vol_or_wac.lower().startswith("v"):
            col_c = volume_column_name
            to_update = "VolumeTables"
            form = volume_formatter
        elif vol_or_wac.lower().startswith("w"):
            col_c = "WAC Sales"
            to_update = "WacTables"
            form = wac_formatter
        else:
            raise ValueError("vol_or_wac needs to be either vol | wac")
        # Dynamically creating the appropriate column names
        col_name = "TTM {}".format(col_c)
        per_col_name = "% of {}".format(col_c)
        # Grabbing the data
        ttm_df = self.generate_ttm_df(unit_name, vol_or_wac)
        # Naming
        ttm_df.index.name = "Drug"
        ttm_df.columns = [col_name]
        ttm_df[col_name] = ttm_df[col_name].round()  # rounding for WAC/Volume
        # Creating percentages
        ttm_df[per_col_name] = ttm_df.apply(lambda col: col / col.sum()).round(2)
        # Appending a total row to the bottom
        ttm_df.loc["Total"] = ttm_df.sum()
        ttm_df.loc["Total", per_col_name] = 1.00
        # Formatting the data into strings
        if convert_to_html:
            ttm_for_data = pd.DataFrame(ttm_df[col_name].apply(form))
            ttm_for_data[per_col_name] = ttm_df[per_col_name].apply(percentage_formatter)
        else:
            ttm_for_data = pd.DataFrame(ttm_df[col_name])
            ttm_for_data[per_col_name] = ttm_df[per_col_name]
        ttm_for_data.reset_index(inplace=True)
        # Formatting the html
        if convert_to_html:
            classes = "report"
            if wide:
                classes += " wide"
            html = ttm_for_data.to_html(index=False).replace("dataframe", classes)
            str_add_on = '<br> <span class="small">(TTM Ended {})</span>'.format(self.ttm_date.strftime("%m/%d/%Y"))
            html = html.replace(col_name, col_name + str_add_on)
            if vol_or_wac.lower().startswith("w"):
                html = html.replace("$", '<span style="float: left;">$</span>')
            self.update_report(to_update, html)
            return html
        else:
            return ttm_for_data

    def rns_report(self, title, convert_to_html=False):
        to_update = "WacTables"
        col_name = "Reported U.S. Net Sales"
        per_col_name = "Net to WAC"
        # Grabbing data
        net_to_wac_df = self.generate_net_to_wac(title)
        # Dropping wav column
        net_to_wac_df.drop("WAC", axis=1, inplace=True)
        # Renaming columns
        net_to_wac_df.index.name = "Drug"
        net_to_wac_df.columns = [col_name, per_col_name]
        # Adding a total row
        net_to_wac_df.loc["Total", "Reported U.S. Net Sales"] = net_to_wac_df["Reported U.S. Net Sales"].sum()
        # Replacing specific nans
        net_to_wac_df["Reported U.S. Net Sales"] = net_to_wac_df["Reported U.S. Net Sales"].fillna("Does not break out U.S. Sales")
        net_to_wac_df.loc[net_to_wac_df["Reported U.S. Net Sales"] == "Does not break out U.S. Sales", "Net to WAC"] = 999999.99
        # Formatting the data into strings
        if convert_to_html:
            net_to_wac_for_df = pd.DataFrame(net_to_wac_df[col_name].apply(wac_formatter))
            net_to_wac_for_df[per_col_name] = net_to_wac_df[per_col_name].apply(percentage_formatter)
        else:
            net_to_wac_for_df = pd.DataFrame(net_to_wac_df[col_name])
            net_to_wac_for_df[per_col_name] = net_to_wac_df[per_col_name]
        # Prepping for html
        net_to_wac_for_df.reset_index(inplace=True)
        # Formatting the html
        if convert_to_html:
            classes = "report"
            html = net_to_wac_for_df.to_html(index=False).replace("dataframe", classes)
            str_add_on = '<br> <span class="small">(TTM Ended {})</span>'.format(self.ttm_date.strftime("%m/%d/%Y"))
            html = html.replace(col_name, col_name + str_add_on)
            html = html.replace("$", '<span style="float: left;">$</span>')
            self.update_report(to_update, html)
            return html
        else:
            return net_to_wac_df

    @staticmethod
    def three_month_volume_summary_html(title, df, last_three_months):
        html = df.to_html(index=False).replace("dataframe", "report volume wide").replace('border="1"', "")
        thead = "<thead>\n"
        index = html.find(thead) + len(thead)
        volume = """<tr>
            <th></th>
            <th colspan='3'>
                {0}
                <br>
                Month Ended:
            </th>
        </tr>
        """.format(title)
        html = html[:index] + volume + html[index:]
        a = False
        for date in last_three_months:
            new_date = date
            month = date[1:3]
            if month[0] == "0":
                new_date = date.replace(month, month[1])
            month_n = month_name[int(month)]
            index = html.find(date)
            html = html[:index] + month_n + "<br>" + html[index:]
            html = html.replace(date, new_date)
        return html

    @staticmethod
    def excel_table_format(df):
        return df.to_html(index=False).replace("dataframe", "report")
