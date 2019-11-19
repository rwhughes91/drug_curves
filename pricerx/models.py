from peewee import *
import os
from pathlib import Path
from playhouse.migrate import *

path = Path(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(path.parent)
DATABASE = os.path.join(BASE_DIR, 'PricerxPrices.db')

db = SqliteDatabase(DATABASE)

"""Price_rx"""
# Creating models for the database


class Base(Model):
    class Meta:
        database = db


class Drug(Base):
    name = CharField()
    manufacturer = CharField()

    def __str__(self):
        return "{0}-{1}".format(self.name, self.manufacturer)


class DrugStrain(Base):
    drug = ForeignKeyField(Drug, backref="strains")
    strength = CharField()
    form = CharField()
    package = IntegerField()
    n = IntegerField()

    def __str__(self):
        return "{0} Strain {1}".format(self.drug, self.n)


class Price(Base):
    strain = ForeignKeyField(DrugStrain, backref="prices")
    drug = ForeignKeyField(Drug, backref="prices")
    date = DateField()
    price = DecimalField()

    def __str__(self):
        return "{0} Price: {1}".format(self.strain, self.price)

    def validated_safe_save(self):
        assert self.drug == self.strain.drug
        self.save()


class Rns(Base):
    date = DateField()
    quarter = CharField()
    net_sales = DecimalField()
    drug = ForeignKeyField(Drug, backref="sales")

    def __str__(self):
        return f"{self.drug}-{self.quarter}-${self.net_sales}"

    def calc_quarter(self):
        year = str(self.date.year)
        month = self.date.month
        if month > 9:
            quarter = 4
        elif month > 6:
            quarter = 3
        elif month > 3:
            quarter = 2
        else:
            quarter = 1
        return f"Q{quarter}'{year[2:]}"


def create_tables(*tables):
    with db:
        safe = {"safe": True}
        for table in tables:
            table.create_table(**safe)


def drop_tables(*tables):
    with db:
        db.drop_tables(tables)


if __name__ == "__main__":
    create_tables(Rns)
