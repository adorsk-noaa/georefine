from georefine.app.projects.models import Project
from georefine.app import db
import os
import imp
import csv

def get_project_schema(project):
	schema_file = os.path.join(project.dir, 'schema.py')
	schema = imp.load_source("gr_project_schema", schema_file)

	# Prefix tables w/ project id.
	for t in schema.metadata.tables.values():
		t.name = "projects{}_{}".format(project.id, t.name)

	return schema

def setUpSchema(project): 
	schema = get_project_schema(project)
	
	# Create tables.
	con = db.engine.connect()
	schema.metadata.create_all(bind=db.session.bind)

	# Load data (in order defined by schema).
	for t in schema.tables:

		# Get the filename for the table.
		table_filename = os.path.join(project.dir, 'data', "{}.csv".format(t['id']))

		# Read records from data file.
		with open(table_filename, 'rb') as table_file:
			reader = csv.DictReader(table_file)
			records = [r for r in reader]

		# @TODO: Do additional processing on records (for geom columns)

		# Insert records.
		db.session.execute(t['table'].insert(), records)
		db.session.commit()


def tearDownSchema(project): 
	schema = get_project_schema(project)
	schema.metadata.drop_all(bind=db.session.bind)




