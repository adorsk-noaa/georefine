from georefine.app.projects.models import Project
from georefine.app import app, db
import georefine.util.shapefile as shp_util
import georefine.util.gis as gis_util
from georefine.app.projects.util.project_dao import ProjectDAO
from sqlalchemy import Column, Float, Integer, String, Boolean, MetaData
from geoalchemy import *
from geoalchemy.geometry import Geometry
from sqlalchemy import create_engine, MetaData
import json
import os, shutil, csv
import pyspatialite
import sys
sys.modules['pysqlite2'] = pyspatialite
import logging
import time
import datetime


class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger
    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

def parse_bool(v):
    if type(v) in [str, unicode]:
        if v.upper() == 'TRUE':
            return True
    try:
        return bool(float(v))
    except:
        return False

def ingest_schema(project, data_dir, session=db.session): 
    schema_code = open(os.path.join(data_dir, "schema.py"), "rU").read()
    compiled_schema = compile(schema_code, '<schema>', 'exec') 
    schema_objs = {}
    exec compiled_schema in schema_objs
    project.schema = schema_objs['schema']

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

def ingest_data(project, data_dir, dao, msg_logger=logging.getLogger(),
                logging_interval=1e4, commit_interval=1e4, 
                progress_logger=logging.getLogger(), **kwargs):
    schema = project.schema

    msg_logger.info("Starting ingest...")

    # Get total count of records from all sources to use for progress.
    msg_logger.info("Counting data records...")
    total_records = 0
    source_counts = {}
    for t in schema['ordered_sources']:
        msg_logger.info("Counting total # of '%s' records..." % t['id'])
        table_filename = os.path.join(data_dir, 'data', "%s.csv" % (t['id']))
        table_file = open(table_filename, 'rU') 
        reader = csv.reader(table_file)
        num_records = 0
        for r in reader: 
            num_records += 1
        msg_logger.info("%s total '%s' records" % (num_records, t['id']))
        source_counts[t['id']] = num_records
        total_records += num_records
        table_file.close()

    # Load data (in order defined by schema).
    progress_counter = 0
    for t in schema['ordered_sources']:

        # Setup source logger.
        source_logger = logging.getLogger("source_%s" % id(t))
        formatter = logging.Formatter(
            "ingesting '%s'..." % t['id'] + ' %(message)s')
        source_log_handler = LoggerLogHandler(msg_logger)
        source_log_handler.setFormatter(formatter)
        source_logger.addHandler(source_log_handler)
        source_logger.setLevel(msg_logger.level)
        source_logger.info("")

        table = t['source']

        # Get the filename for the table.
        table_filename = os.path.join(data_dir, 'data', "%s.csv" % (t['id']))

        # Determine if source has a geometry column. (affects bulk inserts).
        has_geom = False
        for c in table.columns:
            if isinstance(c.type, Geometry):
                has_geom = True
                break

        # Read rows from data file.
        table_file = open(table_filename, 'rU') 
        reader = csv.DictReader(table_file)
        num_records = source_counts[t['id']]
        row_counter = 0
        processed_rows = []
        tran = dao.connection.begin()

        # For time estimates.
        t_start = time.time()
        t_remaining = '---'

        for row in reader:
            row_counter += 1
            progress_counter += 1
            if (row_counter % logging_interval) == 0:
                log_msg = ("row %.1e (%.1f%% of %.1e total, estimated time "
                           "remaining for '%s': %s)") % (
                               row_counter, 100.0 * row_counter/num_records,
                               num_records, t['id'], t_remaining)
                source_logger.info(log_msg)

            if (progress_counter % logging_interval) == 0:
                progress_logger.info(100.0 * progress_counter/total_records)

            processed_row = {}
            # Parse values for columns.
            for c in table.columns:
                # Cast the value per the column's type.
                try:
                    # Defaults.
                    key = c.name

                    # Iniialize stub value for column.
                    processed_row[key] = None

                    cast = str
                    if isinstance(c.type, Float):
                        cast = float
                    elif isinstance(c.type, Integer):
                        cast = int
                    elif isinstance(c.type, Boolean):
                        cast = parse_bool

                    elif isinstance(c.type, Geometry):
                        if row.has_key(c.name + "_wkt"):
                            key = c.name + "_wkt"
                            cast = WKTSpatialElement
                        if row.has_key(c.name + "_wkb"):
                            key = c.name + "_wkb"
                            cast = WKBSpatialElement

                    # Skip column if no corresponding key.
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
                    source_logger.exception("Error")
                    raise Exception, "Error: %s\n Table was: %s, row was: %s, column was: %s, cast was: %s" % (err, table.name, row, c.name, cast)

            processed_rows.append(processed_row)

            # Note: geoalchemy doesn't seem to like bulk inserts yet, so we do
            # geom insert statements one at a time.
            if has_geom:
                dao.connection.execute(t['source'].insert().values(**processed_row))

            if (row_counter % commit_interval) == 0:
                # Do bulk insert for tables w/out geometry columns.
                if not has_geom and processed_rows:
                    dao.connection.execute(t['source'].insert(), processed_rows)
                tran.commit()
                tran = dao.connection.begin()
                processed_rows = []

                # Update time estimates.
                t_now = time.time()
                t_elapsed = t_now - t_start
                t_per_row = t_elapsed/float(row_counter)
                seconds_remaining = (num_records - row_counter) * t_per_row
                t_remaining = datetime.timedelta(seconds=int(seconds_remaining))
        
        # Commit any remaining rows.
        if not has_geom and processed_rows:
            dao.connection.execute(t['source'].insert(), processed_rows)
        tran.commit()

        table_file.close()

def ingest_static_files(project, data_dir):
    static_dir_name = 'static'
    static_files_dir = os.path.join(data_dir, static_dir_name)
    if os.path.isdir(static_files_dir):
        target_dir = os.path.join(project.static_dir, static_dir_name)
        shutil.copytree(
            static_files_dir, 
            os.path.join(project.static_dir, static_dir_name)
        )
        for root, dirs, files in os.walk(target_dir):
            for item in dirs + files:
                os.chmod(os.path.join(root, item), 0775)
