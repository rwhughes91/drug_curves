import os
import pandas as pd

from calendar import month_name

templates = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
template = os.path.join(templates, "tables_template.html")
css = os.path.join(templates, 'css', 'table_styles.css')

with open(template, "r") as f:
    base_html = f.read()

# TODO: function formatters with decorator


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
            "VolumeGraph": 'volume.jpg',
            "PriceGraph": 'price.jpg',
            "WacGraph": 'wac.jpg',
        }
        self.full_report = base_html.replace("(% Title %)", title)

        self.calculated_df = calculated_df
        self.title = title
        self.last_three_months = self.calculated_df.index.unique().sort_values(ascending=False)[:3]
        self.last_month = self.last_three_months[0]

        self.volume_formatter = lambda val: f"{val:,}".replace(".0", "").replace("nan", "")
        self.wac_formatter = lambda val: "$" + f"{val:,}".replace(".0", "").replace("nan", "")
        self.percentage_formatter = lambda val: "{:.0%}".format(val)

        self.calculated_df["Pres Name"] = self.calculated_df["Drug"].str.split(" ").str[0] \
                                          + " (" + self.calculated_df["Manufacturer"] + ")"

    def update_report(self, to_update, html):
        self.counter[to_update]["count"] += 1
        self.counter[to_update]["table_html"].append(html)

    def add_graphs(self, graphs):
        for key, chart in graphs.items():
            escape_char = "(% {} %)".format(key)
            image_tag = '\n    <img src="{}">'.format(chart)
            self.full_report = self.full_report.replace(escape_char, image_tag)

    def generate_report(self):
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
        # Changing thee values for formatted strings
        vol_report = vol_report.applymap(self.volume_formatter)
        # Pushing index out for df.to_html(index=False)
        vol_report.reset_index(inplace=True)
        if convert_to_html:
            html = self.three_month_volume_summary_html(title, vol_report, vol_report.columns[1:])
            self.update_report("VolumeTables", html)
            return html
        else:
            return vol_report

    def annualized_report(self, vol_or_wac, unit_name, n=1, convert_to_html=True, wide=False):
        months = self.calculated_df.index.unique().sort_values(ascending=False)[:n]
        last_month_data = self.calculated_df.loc[months, :].reset_index()
        # Determining if this is a volume or wac report
        if vol_or_wac.lower().startswith("v"):
            col_c = "Vials"
            to_update = "VolumeTables"
            form = self.volume_formatter
        elif vol_or_wac.lower().startswith("w"):
            col_c = "WAC Sales"
            to_update = "WacTables"
            form = self.wac_formatter
        else:
            raise ValueError("vol_or_wac needs to be either vol | wac")
        # Dynamically creating the appropriate column names
        col_name = "Annualized {}".format(col_c)
        per_col_name = "% of {}".format(col_c)
        # Annual-izing the data
        annualized_data = last_month_data.pivot_table(index="Pres Name", values=unit_name,
                                                      aggfunc=lambda ser: (ser.sum() / ser.shape[0]) * 12)
        annualized_data.columns = [col_name]
        annualized_data[col_name] = annualized_data[col_name].round()  # rounding for WAC
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

        # Formatting the data into strings
        annualized_for_data = pd.DataFrame(annualized_data[col_name].apply(form))
        annualized_for_data[per_col_name] = annualized_data[per_col_name].apply(self.percentage_formatter)
        # For df.to_html(index=False)
        annualized_for_data.reset_index(inplace=True)

        if convert_to_html:
            classes = "report"
            if wide:
                classes += " wide"
            html = annualized_for_data.to_html(index=False).replace("dataframe", classes)
            str_add_on = "<br> (Based on Trailing {} Month".format(n)
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
