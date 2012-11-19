from georefine.app.projects.models import Project, MapLayer
from georefine.app import app, db
import georefine.util.shapefile as shp_util
import georefine.util.gis as gis_util
from sqlalchemy import Column, Float, Integer, String, MetaData
from geoalchemy import *
from geoalchemy.geometry import Geometry
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sa_dao.orm_dao import ORM_DAO
import json
import os, shutil, csv


def ingest_schema(project, data_dir, session=db.session): 
    schema_code = open(os.path.join(data_dir, "schema.py"), "rb").read()
    compiled_schema = compile(schema_code, '<schema>', 'exec') 
    schema_objs = {}
    exec compiled_schema in schema_objs
    project.schema = schema_objs['schema']

def ingest_app_config(project, data_dir): 
    app_config_code = open(os.path.join(data_dir, "app_config.py"), "rb").read()
    compiled_app_config= compile(app_config_code, '<app_config>', 'exec') 
    app_config_objs = {}
    exec compiled_app_config in app_config_objs
    project.app_config = app_config_objs['app_config']

def get_dao(project):
    """ Get DAO for a project. """
    project.db_uri = os.path.join(project.dir, 'db.sqlite')
    engine = create_engine(project.db_uri)
    session = scoped_session(sessionmaker(bind=engine))
    dao = ORM_DAO(schema=project.schema, session=session())
    return dao

def ingest_data(project, data_dir, session=db.session):
    schema = project.schema

    # Load data (in order defined by schema).
    for t in schema['ordered_sources']:
        table = t['source']

        # Get the filename for the table.
        table_filename = os.path.join(data_dir, 'data', "%s.csv" % (t['id']))

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
            session.execute(t['source'].insert().values(**processed_row))

        table_file.close()
        session.commit()

def ingest_map_layers(project, source_data_dir, session):
    source_layers_dir = os.path.join(source_data_dir, 'layers')

    target_layers_dir = os.path.join(project.data_dir, "layers")
    os.makedirs(target_layers_dir)

    for layer_id in os.listdir(source_layers_dir):
        source_layer_dir = os.path.join(source_layers_dir, layer_id)

        metadata_file = os.path.join(source_layer_dir, "metadata.json")
        metadata = json.load(open(metadata_file, "rb"))

        target_layer_dir = os.path.join(target_layers_dir, layer_id)
        shutil.copytree(source_layer_dir, target_layer_dir)

        layer_model = MapLayer(
            layer_id=layer_id,
            project=project,
            dir_=target_layer_dir,
            metadata=metadata,
        )
        session.add(layer_model)
    session.commit()

def ingest_static_files(project, data_dir):
    static_dir_name = 'static'
    static_files_dir = os.path.join(data_dir, static_dir_name)
    if os.path.isdir(static_files_dir):
        shutil.copytree(
            static_files_dir, 
            os.path.join(project.static_dir, static_dir_name)
        )
