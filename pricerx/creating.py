import os
import pandas as pd
from pathlib import Path

from pricerx.models import Drug, DrugStrain, Price, db

file = "Norepinephrine Market vRH.xlsx"
sheet_name = "PriceRx_data"

path = Path(os.path.abspath(__file__))
import_dir = os.path.join(os.path.dirname(path.parent), "drug_curves", "imports", file)


def add_prices(df):
    for index, row in df.iterrows():
        drug = Drug.get(name=row["Drug Name"], manufacturer=row["Manufacturer"])
        strain = DrugStrain.get(drug=drug, strength=row["Strength"], form="Vials", package=row["Vials"])
        date = row['Effective Date'].date()
        price = row['Price']
        p = Price(strain=strain, date=date, price=price)
        p.save()


def add_drugs(df):
    unique_drugs = df.groupby(["Drug Name", "Manufacturer"]).size().reset_index(name="size").drop("size", axis=1)
    for index, row in unique_drugs.iterrows():
        drug_name = row["Drug Name"]
        manufacturer = row["Manufacturer"]
        drug = Drug(name=drug_name, manufacturer=manufacturer)
        drug.save()


def add_drugstrain(df):
    unique_strains = df.groupby(["Drug Name", "Manufacturer", "Strength", "Vials"]).size().reset_index(name="size")
    for index, row in unique_strains.iterrows():
        drug = Drug.get(name=row["Drug Name"], manufacturer=row["Manufacturer"])
        n = len(list(drug.strains)) + 1
        strength = row["Strength"]
        form = "Vials"
        package = row["Vials"]
        drugstrain = DrugStrain(drug=drug, strength=strength, form=form, package=package, n=n)
        drugstrain.save()


if __name__ == "__main__":
    data = pd.read_excel(import_dir, sheet_name=sheet_name)
