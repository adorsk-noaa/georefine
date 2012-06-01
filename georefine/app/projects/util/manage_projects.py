from georefine.app.projects.models import Project
from georefine.app import db
from geoalchemy import WKTSpatialElement
import os
import imp
import csv

def getProjectSchema(project):
	schema_file = os.path.join(project.dir, 'schema.py')
	schema = imp.load_source("gr_project_schema", schema_file)

	# Prefix tables w/ project id.
	for t in schema.metadata.tables.values():
		t.name = "projects{}_{}".format(project.id, t.name)

	return schema

def setUpSchema(project): 
	schema = project.schema
	
	# Create tables.
	con = db.engine.connect()
	schema.metadata.create_all(bind=db.session.bind)

def setUpData(project):
	schema = project.schema

	# Load data (in order defined by schema).
	for t in schema.tables:

		# Get the filename for the table.
		table_filename = os.path.join(project.dir, 'data', "{}.csv".format(t['id']))

		# Read records from data file.
		# @TODO: Clean this up later, for things like checking geom type etc.
		with open(table_filename, 'rb') as table_file:
			reader = csv.DictReader(table_file)
			for r in reader:
				r['geom'] = WKTSpatialElement(r['geom'])
				# Note: geoalchemy doesn't seem to like bulk inserts yet, so we do it one at a time.
				db.session.execute(t['table'].insert().values(**r))

		db.session.commit()


def tearDownSchema(project): 
	schema = project.schema
	schema.metadata.drop_all(bind=db.session.bind)




