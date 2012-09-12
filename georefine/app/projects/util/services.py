from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.dao.gr_sa_dao import GeoRefine_SA_DAO
import platform
import copy

def get_dao(project):
    return GeoRefine_SA_DAO(
        connection=db.session.bind, 
        schema=project.schema
    )


# @TODO: Move the logic for fetching connection parms, sql to this function. Take it out of the renderer,
# renderer shouldn't have to do that stuff.
def get_map(project, QUERY, DATA_ENTITY=None, GEOM_ID_ENTITY=None,
            GEOM_ENTITY=None, wms_parameters={}, **kwargs):
    dao = get_dao(project)

    wms_parameters['layers'] = 'data'

    if platform.system() == 'Java':
        from georefine.util.mapping.gt_renderer import (
            GeoToolsMapRenderer, mapSqlAlchemyConnectionParameters)
        gt_renderer = GeoToolsMapRenderer()

        sa_connection_parameters = dao.get_connection_parameters()
        gt_connection_parameters = mapSqlAlchemyConnectionParameters(sa_connection_parameters)

        sql = dao.get_sql(QUERY)

        # Render map image.
        img = gt_renderer.renderMap(
            connection_parameters=gt_connection_parameters,
            sql=sql,
            data_entity=DATA_ENTITY, 
            geom_id_entity=GEOM_ID_ENTITY, 
            geom_entity=GEOM_ENTITY, 
            map_parameters=wms_parameters,
            **kwargs
        )

    # @TODO: Add normal python renderer.
    else:
        from georefine.util.mapping.ms_renderer import MapScriptRenderer
        import georefine.util.mapping.sld_util as sld_util
        renderer = MapScriptRenderer()


        # Generate data string from parameters.
        # Generate styles from parameters.

        if 'postgres' in db.engine.url.drivername:
            connectiontype = 'POSTGIS'

            ms_connection_str = "host=%s password=%s dbname=%s user=%s" % (
                db.engine.url.host, db.engine.url.password, 
                db.engine.url.database, db.engine.url.username)

            sql = dao.get_sql(QUERY)

            ms_data_str = ("geom FROM"
                           " (SELECT ST_SetSRID(subq.%s, 4326) as geom"
                           ", subq.%s as geom_id, *"
                           " FROM (%s) as subq) as wrapped_subq" 
                           " USING UNIQUE geom_id USING srid=4326"
                           % (
                               GEOM_ENTITY['ID'], 
                               GEOM_ID_ENTITY['ID'],
                               sql
                           )
                          )

        elif 'sqlite' in db.engine.url.drivername:
            connectiontype = 'OGR'
            ms_connection_str = db.engine.url.database

            sql = dao.get_sql(QUERY)

            ms_data_str = ("SELECT AsBinary(%s) from %s" 
                           % (
                               GEOM_ENTITY['ID'],
                               sql
                           )
                          )

        # Create SLD for styling if there was a value entity.
        if DATA_ENTITY:
            # Generate class bounds.
            num_classes = DATA_ENTITY.get('num_classes', 25)
            vmin = float(DATA_ENTITY.get('min', 0))
            vmax = float(DATA_ENTITY.get('max', 1))
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
                value_attr=DATA_ENTITY['ID'],
                classes=classes
            )
            
        layers = [{
            'name': 'data',
            'connection': ms_connection_str,
            'connectiontype': connectiontype,
            'data': ms_data_str,
            'projection': 'init=epsg:4326',
            'type': 'POLYGON',
            'sld': {'doc': sld_doc}
        }]

        imgObj = renderer.renderLayers(
            wms_parameters=wms_parameters,
            layers=layers
        )

        img = renderer.imgObj_to_bytes(imgObj)

    return img

    #return open('/data/burger.png').read()

def execute_queries(project, QUERIES=[]):
    dao = get_dao(project)
    results = dao.execute_queries(QUERIES)
    return results

def execute_keyed_queries(project=None, KEY=None, QUERIES=[]):
    dao = get_dao(project)
    keyed_results = dao.get_keyed_results(key_def=KEY, query_defs=QUERIES)
    return keyed_results

