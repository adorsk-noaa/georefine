from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.sa.sa_dao import SA_DAO
import platform
if platform.system() == 'Java':
    from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer
import copy

def get_dao(project):
    return SA_DAO(connection=db.session.bind, schema=project.schema)


# @TODO: Move the logic for fetching connection parms, sql to this function. Take it out of the renderer,
# renderer shouldn't have to do that stuff.
def get_map(project, data_entity=None, geom_id_entity=None, geom_entity=None, grouping_entities=[], filters=[], map_parameters={}, **kwargs):
    dao = get_dao(project)
    renderer = GeoToolsMapRenderer()

    #return open('/data/burger.png').read()
    return renderer.renderMap(
            dao=dao, 
            data_entity=data_entity, 
            geom_id_entity=geom_id_entity, 
            geom_entity=geom_entity, 
            grouping_entities=grouping_entities,
            filters=filters, 
            map_parameters=map_parameters,
            **kwargs
            )

def execute_querys(project, QUERIES=[]):
    dao = get_dao(project)
    return dao.execute_queries(QUERIES)

def execute_keyed_querys(project=None, KEY=None, QUERIES=[]):
    dao = get_dao(project)
    keyed_results = dao.get_keyed_results(key_def=KEY, query_defs=QUERIES)
    return keyed_results

