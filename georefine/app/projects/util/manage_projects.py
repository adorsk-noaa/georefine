from georefine.app.projects.models import Project
from georefine.app import db
from sqlalchemy import Float, Integer
from geoalchemy import Geometry, WKTSpatialElement, WKBSpatialElement
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

        # Get the filename for the table.
        table_filename = os.path.join(project.dir, 'data', "%s.csv" % (t['id']))

        # Read rows from data file.
        table_file = open(table_filename, 'rb') 
        reader = csv.DictReader(table_file)

        for row in reader:
            processed_row = {}
            # Parse values for columns.
            for c in table.columns:
                # Cast the value per the column's type.
                try:
                    # Defaults.
                    key = c.name
                    cast = str
                    if isinstance(c.type, Float):
                        cast = float
                    elif isinstance(c.type, Integer):
                        cast = int
                    elif isinstance(c.type, Geometry):
                        if row.has_key(c.name + "_wkt"):
                            key = c.name + "_wkt"
                            cast = WKTSpatialElement
                        if row.has_key(c.name + "_wkb"):
                            key = c.name + "_wkb"
                            cast = WKBSpatialElement

                    # Skip row if no corresponding key.
                    if not row.has_key(key): 
                        continue

                    # Handle empty values.
                    is_blank = False
                    if cast == float or cast == int:
                        if row[key] == '' or row[key] == None:
                            is_blank = True
                    elif not row[key]: 
                        is_blank = True
                    
                    # Process value if not blank.
                    if not is_blank:
                        processed_row[c.name] = cast(row[key])

                except Exception, err:
                    raise Exception, "Error: %s\n Table was: %s, row was: %s, column was: %s, cast was: %s" % (err, table.name, row, c.name, cast)
            # Insert values.
            # Note: geoalchemy doesn't seem to like bulk inserts yet, so we do it one at a time.
            db.session.execute(t['table'].insert().values(**processed_row))

        table_file.close()
        db.session.commit()


def tearDownSchema(project): 
    schema = project.schema
    schema['metadata'].drop_all(bind=db.session.bind)




