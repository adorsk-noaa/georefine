from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.sa.sa_dao import SA_DAO
import platform
if platform.system() == 'Java':
    from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer, mapSqlAlchemyConnectionParameters
import copy

def get_dao(project):
    return SA_DAO(connection=db.session.bind, schema=project.schema)


# @TODO: Move the logic for fetching connection parms, sql to this function. Take it out of the renderer,
# renderer shouldn't have to do that stuff.
def get_map(project, QUERY, DATA_ENTITY=None, GEOM_ID_ENTITY=None, GEOM_ENTITY=None, MAP_PARAMETERS={}, **kwargs):
    dao = get_dao(project)

    if platform.system() == 'Java':
        # Initialize GeoTools Renderer.
        gt_renderer = GeoToolsMapRenderer()

        # Get connection parameters.
        sa_connection_parameters = dao.get_connection_parameters()
        gt_connection_parameters = mapSqlAlchemyConnectionParameters(sa_connection_parameters)

        # Generate sql.
        sql = dao.get_sql(QUERY)

        # Render map image.
        img = gt_renderer.renderMap(
            connection_parameters = gt_connection_parameters,
            sql = sql,
            data_entity = DATA_ENTITY, 
            geom_id_entity = GEOM_ID_ENTITY, 
            geom_entity = GEOM_ENTITY, 
            map_parameters= MAP_PARAMETERS,
            **kwargs
            )

    # @TODO: Add normal python renderer.
    else:
        img = None

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

