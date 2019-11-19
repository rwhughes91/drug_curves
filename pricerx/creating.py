import os
import pandas as pd
from pathlib import Path

from pricerx.models import Drug, DrugStrain, Price, Rns, db

file = "ALK Inhibitors Market vRH.xlsx"
sheet_name = "RNS"

path = Path(os.path.abspath(__file__))
import_dir = os.path.join(os.path.dirname(path.parent), "drug_curves", "imports", file)


def test_columns(df):
    if list(df.columns) != ["Drug Name", "Manufacturer", "Strength", "Package Size", "Type", "Effective Date", "Price"]:
        raise TypeError("""Columns should be:
                        ['Drug Name', 'Manufacturer', 'Strength', 'Package Size', 'Effective Date', 'Price']""")


def add_prices(df):
    test_columns(df)
    with db:
        for index, row in df.iterrows():
            drug = Drug.get(name=row["Drug Name"], manufacturer=row["Manufacturer"])
            strain = DrugStrain.get(drug=drug, strength=row["Strength"], form=row["Type"], package=row["Package Size"])
            date = row['Effective Date'].date()
            price = row['Price']
            p = Price(strain=strain, drug=drug, date=date, price=price)
            p.validated_safe_save()


def add_drugs(df):
    test_columns(df)
    unique_drugs = df.groupby(["Drug Name", "Manufacturer"]).size().reset_index(name="size").drop("size", axis=1)
    with db:
        for index, row in unique_drugs.iterrows():
            drug_name = row["Drug Name"]
            manufacturer = row["Manufacturer"]
            drug = Drug(name=drug_name, manufacturer=manufacturer)
            drug.save()


def add_drugstrain(df):
    test_columns(df)
    unique_strains = df.groupby(["Drug Name", "Manufacturer", "Strength",
                                 "Package Size", "Type"]).size().reset_index(name="size")
    with db:
        for index, row in unique_strains.iterrows():
            drug = Drug.get(name=row["Drug Name"], manufacturer=row["Manufacturer"])
            n = len(list(drug.strains)) + 1
            strength = row["Strength"]
            form = row["Type"]
            package = row["Package Size"]
            drugstrain = DrugStrain(drug=drug, strength=strength, form=form, package=package, n=n)
            drugstrain.save()


def add_rns(df):
    with db:
        for index, row in df.iterrows():
            drug = Drug.get(name=row["Drug"], manufacturer=row["Manufacturer"])
            date = row["Date"]
            net_sales = row["Reported Net Sales"]
            rns = Rns(drug=drug, date=date, net_sales=net_sales)
            rns.quarter = rns.calc_quarter()
            rns.save()


def add_data(df):
    add_drugs(df)
    add_drugstrain(df)
    add_prices(df)


if __name__ == "__main__":
    data = pd.read_excel(import_dir, sheet_name=sheet_name)
