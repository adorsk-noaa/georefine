from georefine.app import db 
from sqlalchemy import Table, Column, Integer, Text
from sqlalchemy.orm import mapper

class KeyedString(object):
	query = db.session.query_property()

	def __init__(self, id=None, string=None):
		self.id = id
		self.string = string

table = Table('keyed_string_data', db.metadata,
		Column('id', Integer, primary_key=True),
        Column('string', Text),
        )

mapper(KeyedString, table)
