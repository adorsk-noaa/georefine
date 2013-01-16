from georefine.app import app
from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as manage
import georefine.util.mapping.colormap as cmap

from sa_dao.sqlalchemy_dao import SqlAlchemyDAO
import platform
import copy
import tempfile
import tarfile
import os
import logging
import shutil
from StringIO import StringIO

class LoggerLogHandler(logging.Handler):
    """ Custom log handler that logs messages to another
    logger. This can be used to chain together loggers. """
    def __init__(self, logger=None, **kwargs):
        logging.Handler.__init__(self, **kwargs)
        self.logger = logger
    def emit(self, record):
        self.logger.log(record.levelno, self.format(record))

def get_colorbar(colorbar_def, width=100, height=1, format_='GIF'):
    colorbar_img = cmap.generate_colorbar_img(
        width=width, 
        height=height,
        **colorbar_def
    )
    buf = StringIO()
    colorbar_img.save(buf, format=format_)
    return buf.getvalue()

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

def get_layer_map(layer, wms_parameters={}, **kwargs):
    """ Get a map image for a given project layer. """

    # Render w/ GeoTools if using jython.
    if platform.system() == 'Java':
        #@ TODO: implement later...
        pass

    # Otherwise render w/ mapscript.
    else:
        from georefine.util.mapping.ms_renderer import MapScriptRenderer
        renderer = MapScriptRenderer()

        layer_def = {}
        layer_def.update(layer.config)

        # Rewrite relative paths as needed.
        path_attrs = ['mapfile']
        for path_attr in path_attrs:
            path = layer_def.get(path_attr)
            if path:
                layer_def[path_attr] = os.path.join(layer.dir_, path)

        imgObj = renderer.render_map(
            wms_parameters=wms_parameters,
            **layer_def
        )

        img = renderer.imgObj_to_bytes(imgObj)

    return img

def execute_queries(project, QUERIES=[]):
    dao = manage.get_dao(project)
    dao.valid_funcs.append('func.count')
    results = dao.execute_queries(QUERIES)
    return results

def execute_keyed_queries(project=None, KEY=None, QUERIES=[]):
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
        os.makedirs(project.data_dir)
        project.static_dir = os.path.join(app.static_folder, 'projects',
                                          'project_' + str(project.id))
        os.makedirs(project.static_dir)
        progress_logger.info(3)

        # If tarball, unpack project bundle to temp dir.
        tmp_dir = None
        if input_path.endswith('.tar.gz') or input_path.endswith('.tgz'):
            msg_logger.info("Unpacking project file...")
            tmp_dir = tempfile.mkdtemp(prefix="gr.prj_%s." % project.id)
            tar = tarfile.open(input_path)
            tar.extractall(tmp_dir)
            tar.close()
            src_dir = tmp_dir
        else:
            src_dir = input_path
        progress_logger.info(4)

        # Ingest app config.
        msg_logger.info("Ingesting app_config...")
        manage.ingest_app_config(project, src_dir)
        progress_logger.info(5)

        # Ingest project static files.
        msg_logger.info("Ingesting static files...")
        manage.ingest_static_files(project, src_dir)
        progress_logger.info(6)

        # Ingest map layers.
        msg_logger.info("Ingesting map layers...")
        manage.ingest_map_layers(project, src_dir, session)
        progress_logger.info(7)

        # Setup project schema and db.
        msg_logger.info("Setting up project DB...")
        manage.ingest_schema(project, src_dir)
        if not db_uri:
            project.db_uri = "sqlite:///%s" % os.path.join(project.data_dir, "db.sqlite")
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

def delete_project_by_id(project_id=None, **kwargs):
    project = db.session.query(Project).get(project_id)
    if project:
        delete_project(project, **kwargs)

def delete_project(project=None, session=None, logger=logging.getLogger()):
    # Get transactional session.
    if not session:
        session = db.session
    con, trans, session = db.get_session_w_external_trans(session)

    project = session.merge(project)

    try:
        session.delete(project)
        session.commit()
        delete_project_dirs(project)

    except Exception as e:
        trans.rollback()
        raise e

    trans.commit()
    logger.info("Deleted project with id '%s'" % project.id)
    return True

def delete_project_dirs(project):
    for dir_attr in ['data_dir', 'static_dir']:
        dir_ = getattr(project, dir_attr, None)
        if dir_:
            shutil.rmtree(dir_)
