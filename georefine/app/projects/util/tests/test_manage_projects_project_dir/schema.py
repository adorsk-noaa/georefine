from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *
from geoalchemy.postgis import PGComparator

classes = {}
tables = []
metadata = MetaData()
primary_class = None

# Define classes.
class Test1(object):
	def __init__(self, id=None, name=None, geom=None):
		self.id = id
		self.name = name
		self.geom = geom
classes['Test1'] = Test1

# Set primary class.
primary_class = Test1

# Define tables (in dependency order).
test1_table = Table('test1', metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String),
		GeometryExtensionColumn('geom', Polygon(2)),
		)
tables.append({'id': 'test1', 'table': test1_table})
GeometryDDL(test1_table)

# Define mappings.
mapper(
		Test1, 
		test1_table, 
		properties = {
			'geom': GeometryColumn(test1_table.c.geom, comparator=PGComparator),
			}
		)
