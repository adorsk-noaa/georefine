from georefine.app.projects.models import Project
from georefine.app import db
from geoalchemy import WKTSpatialElement
import os
import csv

def getProjectSchema(project):
	schema_file = os.path.join(project.dir, 'schema.py')
	schema_source = open(schema_file, 'rb').read()
	compiled_schema = compile(schema_source, '<schema>', 'exec') 
	schema = {}
	exec compiled_schema in schema

	# Prefix tables w/ project id.
	for t in schema['metadata'].tables.values():
		t.name = "projects%s_%s" % (project.id, t.name)

	return schema

def getProjectAppConfig(project):
	app_config_file = os.path.join(project.dir, 'app_config.py')
	app_config_source = open(app_config_file, 'rb').read()
	compiled_app_config= compile(app_config_source, '<app_config>', 'exec') 
	app_config = {}
	exec compiled_app_config in app_config

	return app_config

def setUpSchema(project): 
	schema = project.schema
	
	# Create tables.
	con = db.engine.connect()
	schema['metadata'].create_all(bind=db.session.bind)

def setUpData(project):
	schema = project.schema

	# Load data (in order defined by schema).
	for t in schema['tables']:

		# Get the filename for the table.
		table_filename = os.path.join(project.dir, 'data', "%s.csv" % (t['id']))

		# Read records from data file.
		# @TODO: Clean this up later, for things like checking geom type etc.
		table_file = open(table_filename, 'rb') 
		reader = csv.DictReader(table_file)
		for r in reader:
			r['id'] = int(r['id'])
			r['geom'] = WKTSpatialElement(r['geom'])
			# Note: geoalchemy doesn't seem to like bulk inserts yet, so we do it one at a time.
			db.session.execute(t['table'].insert().values(**r))
		table_file.close()

		db.session.commit()


def tearDownSchema(project): 
	schema = project.schema
	schema['metadata'].drop_all(bind=db.session.bind)




