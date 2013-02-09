from georefine.app import app
from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as manage
import georefine.util.mapping.colormap as cmap

import json
import platform
import tempfile
from zipfile import ZipFile
import os
import logging
import shutil


class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger
    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

def get_data_map(project, query=None, data_entity=None, geom_id_entity=None,
            geom_entity=None, wms_parameters={}, **kwargs):
    """ Get a map image for a given project data map request. """
    dao = manage.get_dao(project)
    wms_parameters['layers'] = 'data'

    if platform.system() == 'Java':
        from georefine.util.mapping.gt_renderer import (
            GeoToolsMapRenderer, mapSqlAlchemyConnectionParameters)
        gt_renderer = GeoToolsMapRenderer()

        sa_connection_parameters = dao.get_connection_parameters()
        gt_connection_parameters = mapSqlAlchemyConnectionParameters(sa_connection_parameters)

        sql = dao.get_sql(query)

        # Render map image.
        img = gt_renderer.renderMap(
            connection_parameters=gt_connection_parameters,
            sql=sql,
            data_entity=data_entity, 
            geom_id_entity=geom_id_entity, 
            geom_entity=geom_entity, 
            map_parameters=wms_parameters,
            **kwargs
        )

    else:
        from georefine.util.mapping.ms_renderer import MapScriptRenderer
        renderer = MapScriptRenderer()


        # Generate data string from parameters.
        # Generate styles from parameters.

        driver = dao.connection.engine.url.drivername
        if 'postgres' in driver:
            connectiontype = 'POSTGIS'

            ms_connection_str = "host=%s password=%s dbname=%s user=%s" % (
                db.engine.url.host, db.engine.url.password, 
                db.engine.url.database, db.engine.url.username)

            sql = dao.get_sql(query)

            ms_data_str = ("geom FROM"
                           " (SELECT ST_SetSRID(subq.%s, 4326) as geom"
                           ", subq.%s as geom_id, *"
                           " FROM (%s) as subq) as wrapped_subq" 
                           " USING UNIQUE geom_id USING srid=4326"
                           % (
                               geom_entity['ID'], 
                               geom_id_entity['ID'],
                               sql
                           )
                          )

        # Spatialite needs some special handling in order to take advantage
        # of spatial indices.
        elif 'sqlite' in driver:
            connectiontype = 'OGR'
            ms_connection_str = dao.connection.engine.url.database

            #frame_entity = {
                #'EXPRESSION': 'func.BuildMbr(%s)' % wms_parameters['BBOX']
            #}
            #query_obj = dao.get_spatialite_spatial_query(
                #query, geom_entity, frame_entity)
            query_obj = dao.get_query(query)
            sql = dao.query_to_raw_sql(query_obj)

            ms_data_str = "SELECT %s AS 'geometry'" % geom_entity['ID']
            if data_entity:
                ms_data_str += ", %s as 'data'" % data_entity['ID']
            ms_data_str += " FROM (%s) AS 'subq'" % sql
            ms_data_str += " WHERE ST_Intersects(geometry, BuildMbr(%s))" % (
                wms_parameters['BBOX'])

        # Create classes for styling if there was a data entity.
        if data_entity:

            # Generate color bins.
            color_bins = cmap.generate_colored_bins(
                schema= 'rgb',
                vmin=data_entity.get('vmin', 0),
                vmax=data_entity.get('vmax', 1),
                num_bins=data_entity.get('num_bins', 20),
                colormap=data_entity.get(
                    'colormap', cmap.generate_hsv_bw_colormap()
                ),
                include_bins=data_entity.get('include_bins', []),
                include_values=data_entity.get('include_values', []),
            )

            # Add bottom/top bins.
            color_bins.insert(0, ((None, color_bins[0][0][0]), color_bins[0][1]))
            color_bins.append(((color_bins[-1][0][1], None), color_bins[-1][1]))

            # Create classes from color bins.
            classes = []
            for color_bin in color_bins:
                bin_ = color_bin[0]
                cmin = bin_[0]
                cmax = bin_[1]
                color = color_bin[1]
                if cmin is not None and cmax is not None:
                    cls = {
                        'expression': "(([data] >= %s) AND ([data] < %s))" % (
                            cmin, cmax),
                        'style': {
                            'color': color
                        }
                    }
                elif cmin is None and cmax is not None:
                    cls = {
                        'expression': "([data] < %s)" % (cmax),
                        'style': {
                            'color': color
                        }
                    }
                elif cmin is not None and cmax is None:
                    cls = {
                        'expression': "([data] >= %s)" % (cmin),
                        'style': {
                            'color': color
                        }
                    }
                classes.append(cls)

        layers = [{
            'name': 'data',
            'connection': ms_connection_str,
            'connectiontype': connectiontype,
            'data': ms_data_str,
            'projection': 'init=epsg:4326',
            'type': 'POLYGON',
            'classes': classes,
        }]

        imgObj = renderer.render_map(
            # use random bg color for transparency
            # Otherwise it defaults to white.
            imagecolor=(253, 27, 92),
            wms_parameters=wms_parameters,
            layers=layers,
        )
        img = renderer.imgObj_to_bytes(imgObj)

    return img

def get_layer_map(project, layer_id, wms_parameters={}, **kwargs):
    """ Get a map image for a given project layer. """

    # @TODO: implicit convention? maybe should centralize layer dir...
    layer_dir = os.path.join(project.static_dir, 'static', 'map_layers', layer_id)

    # Read layer WMS config.
    config_path = os.path.join(layer_dir, 'wms.json')
    with open(config_path, 'rb') as f:
        wms_config = json.load(f)

    # Render w/ GeoTools if using jython.
    if platform.system() == 'Java':
        #@ TODO: implement later...
        pass

    # Otherwise render w/ mapscript.
    else:
        from georefine.util.mapping.ms_renderer import MapScriptRenderer
        renderer = MapScriptRenderer()

        # Rewrite relative paths as needed.
        path_attrs = ['mapfile']
        for path_attr in path_attrs:
            path = wms_config.get(path_attr)
            if path:
                wms_config[path_attr] = os.path.join(layer_dir, path)

        imgObj = renderer.render_map(
            wms_parameters=wms_parameters,
            **wms_config
        )

        img = renderer.imgObj_to_bytes(imgObj)

    return img

def execute_queries(project, QUERIES=[]):
    dao = manage.get_dao(project)
    dao.valid_funcs.append('func.count')
    results = dao.execute_queries(QUERIES)
    return results

def execute_keyed_queries(project, KEY=None, QUERIES=[]):
    dao = manage.get_dao(project)
    keyed_results = dao.get_keyed_results(key_def=KEY, query_defs=QUERIES)
    return keyed_results


def create_project(input_path=None, msg_logger=logging.getLogger(), 
                   progress_logger=logging.getLogger(), session=None, 
                   db_uri=None, **kwargs):
    """ Create a project from a project bundle file. """
    # Get transactional session.
    if not session:
        session = db.session()
    con, trans, session = db.get_session_w_external_trans(
        session, new_connection=True)

    try:
        # Create project model.
        msg_logger.info("Initializing project...")
        project = Project()
        session.add(project)
        session.commit()
        progress_logger.info(2)

        # Create project directories.
        msg_logger.info("Setting up project directories...")
        project.data_dir = os.path.join(app.config['DATA_DIR'], 'projects',
                                   'project_' + str(project.id))
        os.makedirs(project.data_dir, 0775)
        project.static_dir = os.path.join(app.static_folder, 'projects',
                                          'project_' + str(project.id))
        os.makedirs(project.static_dir, 0775)
        progress_logger.info(3)

        # If .zip, unpack project bundle to temp dir.
        tmp_dir = None
        if input_path.endswith('.zip'):
            msg_logger.info("Unpacking project file...")
            tmp_dir = tempfile.mkdtemp(prefix="gr.prj_%s." % project.id)
            zfile = ZipFile(input_path, 'r')
            zfile.extractall(tmp_dir)
            zfile.close()
            src_dir = tmp_dir
        else:
            src_dir = input_path
        progress_logger.info(4)

        # Ingest project static files.
        msg_logger.info("Ingesting static files...")
        manage.ingest_static_files(project, src_dir)
        progress_logger.info(6)

        # Setup project schema and db.
        msg_logger.info("Setting up project DB...")
        manage.ingest_schema(project, src_dir)
        if not db_uri:
            db_file = os.path.join(project.data_dir, "db.sqlite")
            project.db_uri = "sqlite:///%s" % db_file
            manage.initialize_db(project)
            os.chmod(db_file, 0775)
        else:
            project.db_uri = db_uri
            manage.initialize_db(project)
        dao = manage.get_dao(project)
        dao.create_all()
        progress_logger.info(8)

        # Setup ingest msg logger.
        ingest_msg_logger = logging.getLogger("ingest_msg_%s" % id(project))
        formatter = logging.Formatter("Ingesting data..." + ' %(message)s')
        ingest_msg_log_handler = LoggerLogHandler(msg_logger)
        ingest_msg_log_handler.setFormatter(formatter)
        ingest_msg_logger.addHandler(ingest_msg_log_handler)
        ingest_msg_logger.setLevel(msg_logger.level)

        # Setup ingest progress logger to scale progress.
        class ScalingProgressHandler(logging.Handler):
            def __init__(self, logger=None, min_=0.0, max_=100.0, **kwargs):
                logging.Handler.__init__(self, **kwargs)
                self.logger = logger
                self.max = max_
                self.min = min_
                self.range = max_ - min_
            def emit(self, record):
                value = float(self.format(record))
                scaled_value = self.min + self.range * (value/100.0)
                self.logger.log(record.levelno, scaled_value)

        ingest_prg_logger = logging.getLogger("ingest_prg_%s" % id(project))
        ingest_prg_log_handler = ScalingProgressHandler(progress_logger,
                                                        min_=8, max_=99)
        ingest_prg_logger.addHandler(ingest_prg_log_handler)
        ingest_prg_logger.setLevel(progress_logger.level)

        # Ingest data.
        ingest_kwargs = kwargs.get('ingest_kwargs', {})
        manage.ingest_data(project, src_dir, dao, msg_logger=ingest_msg_logger,
                           progress_logger=ingest_prg_logger, **ingest_kwargs)

        # Clean up tmpdir (if created).
        if tmp_dir:
            shutil.rmtree(tmp_dir)

        session.commit()
        trans.commit()

    except Exception as e:
        msg_logger.exception("Error creating project.")
        try:
            pass
            if project:
                delete_project_dirs(project)
            if tmp_dir:
                shutil.rmtree(tmp_dir)
        except NameError:
            pass
        trans.rollback()
        raise e

    msg_logger.info("Project with id '%s' been created." % project.id)
    progress_logger.info(100)
    return project

def delete_project_by_id(project_id=None, logger=logging.getLogger(), **kwargs):
    project = db.session.query(Project).get(project_id)
    if project:
        delete_project(project, logger=logger, **kwargs)
    else:
        logger.info("Project with id '%s' did not exist." % project_id)

def delete_project(project=None, session=None, logger=logging.getLogger()):
    # Get transactional session.
    if not session:
        session = db.session
    project = session.merge(project)
    delete_project_dirs(project)
    session.delete(project)
    session.commit()
    logger.info("Deleted project with id '%s'" % project.id)
    return True

def delete_project_dirs(project):
    for dir_attr in ['data_dir', 'static_dir']:
        dir_ = getattr(project, dir_attr, None)
        if dir_ and os.path.isdir(dir_):
            shutil.rmtree(dir_)
