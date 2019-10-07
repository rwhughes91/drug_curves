from peewee import *
import os
from pathlib import Path

path = Path(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(path.parent)
DATABASE = os.path.join(BASE_DIR, 'PricerxPrices.db')

db = SqliteDatabase(DATABASE)


# Creating models for the database
class Base(Model):
    class Meta:
        database = db


class Drug(Base):
    name = CharField()


class DrugStrain(Base):
    drug = ForeignKeyField(Drug, backref="strains")
    strength = CharField()
    form = CharField()
    package = IntegerField()


class Price(Base):
    strain = ForeignKeyField(DrugStrain, backref="prices")
    date = DateField()
    price = DecimalField()


def add_data(df, drug_strain):
    for index, row in df.iterrows():
        date = row['Date'].date()
        price = row['Price']
        p = Price(strain=drug_strain, date=date, price=price)
        p.save()


def create_tables():
    Drug.create_table(safe=True)
    DrugStrain.create_table(safe=True)
    Price.create_table(safe=True)


if __name__ == "__main__":
    db.connect()
    db.close()
