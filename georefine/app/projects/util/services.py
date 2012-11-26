from georefine.app import app
from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as manage
import georefine.util.mapping.sld_util as sld_util
from sa_dao.sqlalchemy_dao import SqlAlchemyDAO
import platform
import copy
import tempfile
import tarfile
import os
import logging
import shutil


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

        # Create SLD for styling if there was a value entity.
        if data_entity:
            # Generate class bounds.
            num_classes = data_entity.get('NUM_CLASSES', 25)
            vmin = float(data_entity.get('MIN', 0))
            vmax = float(data_entity.get('MAX', 1))
            vrange = vmax - vmin
            class_width = vrange/num_classes
            classes = [[None, vmin]]
            for i in range(num_classes):
                classes.append([vmin + i * class_width, 
                                vmin + (i + 1) * class_width])
            classes.append([vmax, None])

            # Render sld.
            sld_doc = sld_util.get_polygon_gradient_sld(
                layer_name='data',
                value_attr='data',
                classes=classes
            )

        layers = [{
            'name': 'data',
            'connection': ms_connection_str,
            'connectiontype': connectiontype,
            'data': ms_data_str,
            'projection': 'init=epsg:4326',
            'type': 'POLYGON',
            'apply_sld': [sld_doc, 'data'],
        }]

        imgObj = renderer.render_map(
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
        layer_def.update(layer.metadata)

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


def create_project(project_file=None, logger=logging.getLogger(), 
                   session=None):
    """ Create a project from a project bundle file. """
    # Get transactional session.
    if not session:
        session = db.session()
    con, trans, session = db.get_session_w_external_trans(
        session, new_connection=True)

    try:
        # Create project model.
        project = Project()
        session.add(project)
        session.commit()

        # Create project directories.
        project.data_dir = os.path.join(app.config['DATA_DIR'], 'projects',
                                   'project_' + str(project.id))
        os.makedirs(project.data_dir)
        project.static_dir = os.path.join(app.static_folder, 'projects',
                                          'project_' + str(project.id))
        os.makedirs(project.static_dir)

        # Unpack project bundle to temp dir.
        tmp_dir = tempfile.mkdtemp(prefix="gr.prj_%s." % project.id)
        tar = tarfile.open(project_file)
        tar.extractall(tmp_dir)
        tar.close()

        # Ingest app config.
        manage.ingest_app_config(project, tmp_dir)

        # Ingest project static files.
        manage.ingest_static_files(project, tmp_dir)

        # Ingest map layers.
        manage.ingest_map_layers(project, tmp_dir, session)

        # Setup project schema and db.
        manage.ingest_schema(project, tmp_dir)
        project.db_uri = "sqlite:///%s" % os.path.join(project.data_dir, "db.sqlite")
        manage.initialize_db(project)
        dao = manage.get_dao(project)
        dao.create_all()
        manage.ingest_data(project, tmp_dir, dao)

        # Clean up tmpdir.
        shutil.rmtree(tmp_dir)

        session.commit()
        trans.commit()

    except Exception as e:
        logger.exception("Error creating project.")
        try:
            if project:
                delete_project_dirs(project)
            shutil.rmtree(tmp_dir)
        except NameError:
            pass
        trans.rollback()
        raise e

    return project

def delete_project(project, session=None):
    """ Delete a project. """
    # Get transactional session.
    if not session:
        session = db.session
    con, trans, session = db.get_session_w_external_trans(session)

    project = session.merge(project)

    try:
        delete_project_dirs(project)
        session.delete(project)
        session.commit()

    except Exception as e:
        trans.rollback()
        raise e

    trans.commit()
    return True

def delete_project_dirs(project):
    for dir_attr in ['data_dir', 'static_dir']:
        dir_ = getattr(project, dir_attr, None)
        if dir_:
            shutil.rmtree(dir_)
