from georefine.app.projects.models import Project
from georefine.app import db
from sqlalchemy import Float, Integer
from geoalchemy import Geometry, WKTSpatialElement
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
    schema = getProjectSchema(project)
    
    # Create tables.
    con = db.engine.connect()
    schema['metadata'].create_all(bind=db.session.bind)

def setUpData(project):
    schema = getProjectSchema(project)

    # Load data (in order defined by schema).
    for t in schema['tables']:

        table = t['table']
        for c in table.columns:
            print type(c.type)
            print c.name

        # Get the filename for the table.
        table_filename = os.path.join(project.dir, 'data', "%s.csv" % (t['id']))

        # Read rows from data file.
        table_file = open(table_filename, 'rb') 
        reader = csv.DictReader(table_file)

        for row in reader:
            processed_row = {}
            # Parse values for columns.
            for c in table.columns:
                if row.has_key(c.name):
                    # Cast the value per the column's type.
                    if isinstance(c.type, Float):
                        value = float(row[c.name])
                    elif isinstance(c.type, Integer):
                        value = int(row[c.name])
                    elif isinstance(c.type, Geometry):
                        if row.has_key(c.name + "_wkt"):
                            value = WKBSpatialElement(row[c.name + "_wkt"])
                        if row.has_key(c.name + "_wkb"):
                            value = WKTSpatialElement(row[c.name + "_wkb"])
                    else:
                        value = str(row[c.name])
                    processed_row[c.name] = value

            # Insert values.
            # Note: geoalchemy doesn't seem to like bulk inserts yet, so we do it one at a time.
            db.session.execute(t['table'].insert().values(**processed_row))

        table_file.close()
        db.session.commit()


def tearDownSchema(project): 
    schema = project.schema
    schema['metadata'].drop_all(bind=db.session.bind)




