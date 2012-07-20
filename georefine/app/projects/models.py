from georefine.app import db 
from sqlalchemy import Table, Column, Integer, String
from sqlalchemy.orm import mapper

class Project(object):
	query = db.session.query_property()

	def __init__(self, id=None, name=None, dir=None):
		self.id = id
		self.name = name
		self.dir = dir

project_table = Table('project_projects', db.metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String),
		Column('dir', String),
		)

mapper(Project, project_table)
