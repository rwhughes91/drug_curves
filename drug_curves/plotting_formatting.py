import math
import operator
import locale

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
    "black": (89, 89, 89),
    "red": (192, 0, 0)
}


def plt_color_conversion(mapper):
    adj_color_mapper = {}
    for key, value in mapper.items():
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


def sort_legend(array):
    # Creating number of columns to create in legend
    ncols = math.ceil(len(array) / 2)
    sorted_legend = []
    for x, y in zip_longest(array[:ncols], array[ncols:]):
        sorted_legend.append(x)
        # If odd number last item will be None
        if y:
            sorted_legend.append(y)

    return zip(*sorted_legend)


def organize_legend(ax):
    handles, labels = ax.get_legend_handles_labels()
    h = list(sorted(zip(handles, labels), key=operator.itemgetter(1)))
    handles2, labels2 = sort_legend(h)
    ax.legend(handles2, labels2, loc="upper center", ncol=math.ceil(len(h) / 2), bbox_to_anchor=(.47, -0.12), frameon=False)


""" Pricing graph"""


if __name__ == "__main__":
    d = round_pricerx_prices(pricerx_data_fetching(["Levophed Bitartrate", "Norepinephrine Bitartrate"]))
