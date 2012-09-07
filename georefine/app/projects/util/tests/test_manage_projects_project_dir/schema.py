from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *

tables = {}
ordered_tables = []
metadata = MetaData()

# Define tables in dependency order.
tables['test1'] = Table('test1', metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String),
		GeometryExtensionColumn('geom', Polygon(2)),
		)
GeometryDDL(tables['test1'])
ordered_tables.append(tables['test1'])

