from xlsxwriter.utility import xl_rowcol_to_cell, xl_col_to_name


def excel_export(writer, frames, labels, color_plotting_map):
    formats = {
        "volume": {"num_format": "#,##0_);(#,##0)"},
        "money": {"num_format": '_($* #,##0_);_($* (#,##0);_($* "-"??_);_(@_)'},
    }
    tabs = ["volume", "pricerx", "wac"]
    # Adding styles to the workbook
    workbook = writer.book
    volume_format = workbook.add_format(formats["volume"])
    money_format = workbook.add_format(formats["money"])
    header_format = workbook.add_format({
        'bold': True,
        'border': 1,
        'fg_color': "#1F497D",
        'font_color': "white",
        'align': "center",
        "valign": "vcenter",
    })
    header_format.set_text_wrap()

    # Writing the data
    for tab in tabs:
        if tab == "volume":
            body_format = volume_format
        else:
            body_format = money_format
        frame = frames[tab]
        # Writing the df
        frame.to_excel(writer, sheet_name=tab, index=False)
        edit_sheet = writer.sheets[tab]
        # Styling the numbers of the cells
        edit_sheet.set_column(0, len(frame.columns) - 1, 13, body_format)
        # Styling the columns
        for col_name, value in enumerate(frame.columns.values):
            edit_sheet.write(0, col_name, value, header_format)

        # Writing the charts
        chart = workbook.add_chart({"type": "line"})

        # For loop here to dynamically plot the series
        last_row = frame.shape[0] + 1
        categories = f"={tab}!$A$2:$A${last_row}"
        for i in range(1, len(frame.columns)):
            col = xl_col_to_name(i)
            name = f"={tab}!${col}1"
            values = f"={tab}!${col}$2:${col}${last_row}"
            settings = {
                'name': name,
                'categories': categories,
                'values': values,
                "line": {"width": 2.25, "color": color_plotting_map[frame.columns[i]]}
            }
            if frame.columns[i] == "Total":
                settings["line"] = {"width": 2.25, "dash_type": "round_dot",
                                    "color": color_plotting_map[frame.columns[i]]}
            chart.add_series(settings)

        # Customizing the charts
        # Setting the axis
        color = "#595959"
        chart.set_title({"name": labels[tab]["title"],
                         "name_font": {'bold': False, 'size': 14, 'color': color}})
        chart.set_x_axis({"name": "Source: Symphony Health Solutions",
                          "name_font": {'bold': False, 'color': color},
                          "num_font": {'bold': False, 'rotation': -45, 'color': color},
                          "date_axis": True})
        chart.set_y_axis({"name": labels[tab]["y-axis"],
                          "name_font": {"bold": False, 'color': color},
                          "num_font": {"color": color},
                          "line": {"none": True},
                          "major_gridlines": {"visible": True, "line": {"width": 0.75, "color": "#d9d9d9"}}})
        # Setting the legend
        chart.set_legend({"position": "bottom",
                          "font": {"color": color}})

        # Writing the chart (dynamically create based off of length)
        chart_placement = xl_rowcol_to_cell(3, len(frame.columns) + 1)
        edit_sheet.insert_chart(chart_placement, chart, {'x_scale': 2, 'y_scale': 2})

    frames["raw_data"].to_excel(writer, sheet_name="raw_data", index=False)

    # Saving the file and closing stream
    writer.save()
