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
    date = DateField()
    price = DecimalField()

    def __str__(self):
        return "{0} Price: {1}".format(self.strain, self.price)


def create_tables():
    Drug.create_table(safe=True)
    DrugStrain.create_table(safe=True)
    Price.create_table(safe=True)
