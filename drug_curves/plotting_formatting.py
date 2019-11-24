import math
import operator
import locale

import pandas as pd
from itertools import zip_longest
from matplotlib.ticker import FuncFormatter
from matplotlib.dates import DateFormatter

from drug_curves.curve_functions import pricerx_data_fetching, round_pricerx_prices

"""Colors"""
color_map_universal = {
    "purple": (112, 48, 160),
    "blue": (91, 155, 213),
    "green": (112, 173, 71),
    "yellow": (255, 192, 0),
    "orange": (237, 125, 49),
    "grey": (128, 128, 128),
    "blue-grey": (51, 63, 79),
    "black": (66, 66, 66),
    "red": (192, 0, 0)
}


def clamp(*x):
    values = []
    for l in x:
        values.append(max(0, min(l, 255)))
    return values


def plt_color_conversion(mapper, type_f="plt"):
    adj_color_mapper = {}
    for key, value in mapper.items():
        if type_f == "hex":
            adj_color_mapper[key] = "#{0:02x}{1:02x}{2:02x}".format(*clamp(*value))
        else:
            adj_color_mapper[key] = tuple(c/255 for c in value)
    return adj_color_mapper


"""Plotting"""


def add_label_key(plotting_map):
    for key, items in plotting_map.items():
        for manuf, data in items.items():
            if type(data) == tuple:
                pass
            else:
                label = key.split(" ")[0]
                data["label"] = "{0} ({1})".format(label, manuf)
    plotting_map["Total"]["label"] = "Total"


def plot_graph(ax, df, mapper):
    for drug, manufacturer in df:
        keywords = {}
        if drug == "Total":
            data = mapper[drug]
            keywords["ls"] = "dotted"
        else:
            data = mapper[drug][manufacturer]
        keywords["c"] = data["color"]
        keywords["label"] = data["label"]
        ax.plot(df[(drug, manufacturer)], **keywords)


"""Formatting y axis"""


def y_tick_label_formatter(type):
    locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
    if type == "volume":
        def format_fn_volume(tick_val, tick_pos):
            return locale.currency(tick_val, grouping=True).replace(".00", "").replace("$", "")
        return FuncFormatter(format_fn_volume)
    elif type == "wac":
        def format_fn_wac(tick_val, tick_pos):
            return locale.currency(tick_val, grouping=True).replace(".00", "")
        return FuncFormatter(format_fn_wac)
    else:
        raise TypeError("Type needs to be 'volume' or 'wac'")


def y_axis_formatter(ax, lim, base, type):
    assert base.max() < lim
    ax.set_ylim(0, lim)
    ax.yaxis.set_major_formatter(y_tick_label_formatter(type))
    ax.yaxis.grid(True)


"""Formatting x axis"""


def x_axis_formatter(ax, base):
    ax.set_xticks(list(base.index)[::-2])
    ax.set_xlim([base.index[0], base.index[-1]])
    years_fmt = DateFormatter("%m/%d/%Y")
    ax.xaxis.set_major_formatter(years_fmt)


"""Other plot aesthetics"""


def excelify(ax):
    # Modifying tick size and aesthetics
    ax.tick_params(left=False)
    ax.tick_params(axis="x", labelsize=10)
    ax.tick_params(axis="y", labelsize="medium")

    # Modifying spines
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color('grey')


"""Formatting the legend"""


def sort_legend_labels(handle_label):
    label = handle_label[1]
    if label == "Total":
        return "Zzzzzzzzz"
    else:
        return label


def sort_legend(array):
    # Creating number of columns to create in legend
    ncols = math.ceil(len(array) / 2)
    sorted_legend = []
    last_item = array[-1]
    array = array[:-1]
    for x, y in zip_longest(array[:ncols], array[ncols:]):
        sorted_legend.append(x)
        # If odd number last item will be None
        if y:
            sorted_legend.append(y)
    if ncols % 2 == 0:
        i = len(sorted_legend)
    else:
        i = len(sorted_legend) - 1
    sorted_legend.insert(i, last_item)
    return zip(*sorted_legend)


def organize_legend(ax):
    handles, labels = ax.get_legend_handles_labels()
    h = list(sorted(zip(handles, labels), key=sort_legend_labels))
    if len(h) > 5:
        ncol = math.ceil(len(h) / 2)
        handles2, labels2 = sort_legend(h)
    else:
        ncol = len(h)
        handles2, labels2 = handles, labels
    ax.legend(handles2, labels2, loc="upper center", ncol=ncol, bbox_to_anchor=(.47, -0.13), frameon=False)


""" Pricing graph"""


def finding_pct_changes(drug, manufacturer, df):
    df_slice = df[[(drug, manufacturer)]].copy()
    df_slice.columns = ["Price"]
    df_slice["Pct_change"] = df_slice["Price"].pct_change().round(2)
    return df_slice.loc[df_slice["Pct_change"] > 0, :].copy()


def percentage_annotation(ax, df, offset=None, offset_x=0, offset_y=0, arrow=False, **kwargs):
    """
    If positional offset is applied to function, and it is a midpoint, the global offsets will not be applied to that
    annotation
    :param ax:
    :param df:
    :param offset: {
            pos: {
                coord_offset: (x, y),
                midpoint: (False, True)
            },
            pos2: ...
        }
    :param offset_x: global shifts on x axis (in weeks)
    :param offset_y: global shifts on y axis
    """
    if offset:
        if type(offset) != dict:
            raise TypeError("offset needs to be a map specifying index and offset for particular percentage")

    # storing argument input to reset for each iteration
    xx = offset_x
    yy = offset_y

    coords = []
    for i, (index, row) in enumerate(df.iterrows()):
        # Clearing offsets
        offset_x = xx  # will equal function argument again
        offset_y = yy  # will equal function argument again

        # Calculating mid_point & creating input variables
        date = index
        new_price = row["Price"]
        pct_change = row["Pct_change"]
        old_price = new_price / (1 + pct_change)
        mid_point = (new_price + old_price) / 2

        # Applying specific positioned offset(s)
        if offset:
            if i in offset:
                x, y = offset[i]["coord_offset"]
                if "midpoint" in offset[i]:
                    x_d, x_m = offset[i]["midpoint"]
                    if x_d:
                        date = x
                        offset_x = 0
                        x = 0
                    if x_m:
                        mid_point = y
                        offset_y = 0
                        y = 0
                offset_x += x
                offset_y += y

        # Applying all offsets
        if offset_x > 0:
            date += pd.Timedelta(weeks=offset_x)
        elif offset_x < 0:
            date += pd.Timedelta(weeks=offset_x)
        if offset_y > 0:
            mid_point += offset_y
        elif offset_y < 0:
            mid_point += offset_y

        # Formatting as a percentage
        percentage = "{0:.0%}".format(pct_change)
        # Annotating the graph
        coords.append((date, mid_point))
        ax.text(date, mid_point, percentage, **kwargs)
        # Applying Arrows
        if arrow:
            di = index
            m = (new_price + old_price) / 2
            if offset:
                if i in offset:
                    if offset[i]["arrow_offset"]:
                        bot_x, top_x, bot_y, top_y = offset[i]["arrow_offset"]
                        di += pd.Timedelta(weeks=bot_x)
                        date += pd.Timedelta(weeks=top_x)
                        m += bot_y
                        mid_point += top_y
            ax.annotate("", xytext=(date, mid_point), xy=(di, m),
                        arrowprops={
                            "color": kwargs["color"],
                            "lw": 1.5,
                            "arrowstyle": "->"
                        })
    return coords


if __name__ == "__main__":
    d = round_pricerx_prices(pricerx_data_fetching(["Levophed Bitartrate", "Norepinephrine Bitartrate"]))
    e = plt_color_conversion(color_map_universal, type_f="hex")
