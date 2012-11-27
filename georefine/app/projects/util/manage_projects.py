from georefine.app.projects.models import Project, MapLayer
from georefine.app import app, db
import georefine.util.shapefile as shp_util
import georefine.util.gis as gis_util
from georefine.app.projects.util.project_dao import ProjectDAO
from sqlalchemy import Column, Float, Integer, String, MetaData
from geoalchemy import *
from geoalchemy.geometry import Geometry
from sqlalchemy import create_engine, MetaData
import json
import os, shutil, csv
import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import logging


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
    engine = get_engine(project)
    dao = ProjectDAO(schema=project.schema, connection=engine.connect())
    return dao

def get_engine(project, **kwargs):
    return create_engine(project.db_uri, **kwargs)

def initialize_db(project):
    if project.db_uri.startswith('sqlite'):
        engine = get_engine(project)
        con = engine.connect()
        con.execute("SELECT InitSpatialMetaData()")

def ingest_data(project, data_dir, dao, logger=logging.getLogger(),
                logging_interval=1000, commit_interval=10000):
    schema = project.schema

    logger.info("Starting ingest...")

    # Load data (in order defined by schema).
    for t in schema['ordered_sources']:
        logger.info("Ingesting data for source '%s'" % t['id'])
        table = t['source']

        # Get the filename for the table.
        table_filename = os.path.join(data_dir, 'data', "%s.csv" % (t['id']))

        # Read rows from data file.
        table_file = open(table_filename, 'rb') 
        reader = csv.DictReader(table_file)

        tran = dao.connection.begin()

        row_counter = 0
        for row in reader:
            row_counter += 1
            if (row_counter % logging_interval) == 0:
                logger.info("row %d" % row_counter)

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
            dao.connection.execute(t['source'].insert().values(**processed_row))

            if (row_counter % commit_interval) == 0:
                tran.commit()
                tran = dao.connection.begin()
        
        # Commit any remaining rows.
        tran.commit()

        table_file.close()

def ingest_map_layers(project, source_data_dir, session):
    layers_data_dir = os.path.join(source_data_dir, 'data', 'map_layers', 'data')

    if not os.path.exists(layers_data_dir):
        return

    target_layers_dir = os.path.join(project.data_dir, "map_layers")
    os.makedirs(target_layers_dir)

    map_layers_file = os.path.join(layers_data_dir, "map_layers.csv")
    reader = csv.DictReader(open(map_layers_file, "rb"))
    layers = [row for row in reader]

    for layer in layers:
        source_layer_dir = os.path.join(layers_data_dir, layer['id'])

        metadata_file = os.path.join(source_layer_dir, "metadata.json")
        if os.path.exists(metadata_file):
            metadata = json.load(open(metadata_file, "rb"))
        else:
            metadata = {}

        target_layer_dir = os.path.join(target_layers_dir, layer['id'])
        shutil.copytree(source_layer_dir, target_layer_dir)

        layer_model = MapLayer(
            layer_id=layer['id'],
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
