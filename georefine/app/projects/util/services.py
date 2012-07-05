from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.sa.sa_dao import SA_DAO
import platform
if platform.system() == 'Java':
	from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer
import copy

def get_dao(project):
	return SA_DAO(session=db.session, primary_class=project.schema['primary_class'])

def get_entities(project):
	dao = get_dao(project)
	return dao.get_entities()

# @TODO: Better name for this??
# Just executes a regular non-aggregate query.
def query(project, select_entities=[], grouping_entities=[], sorting_entities=[], filters=[]):
    dao = get_dao(project)
    results = dao.execute_query(dat
    


# @TODO: Move the logic for fetching connection parms, sql to this function. Take it out of the renderer,
# renderer shouldn't have to do that stuff.
def get_map(project, data_entity=None, geom_id_entity=None, geom_entity=None, grouping_entities=[], filters=[], map_parameters={}):
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
			map_parameters=map_parameters
			)

def get_aggregates(project, data_entities=[], grouping_entities=[], filters=[], with_unfiltered=False, base_filters=[]):
	dao = get_dao(project)

	# Set default id/label.
	for data_entity in data_entities:
		data_entity.setdefault('id', str(id(data_entity)))
		data_entity.setdefault('label', data_entity['id'])

	# Get filtered aggregates.
	aggregates = dao.get_aggregates(
			data_entities = data_entities,
			grouping_entities = grouping_entities,
			filters = filters
			)

	# Add unfiltered aggregates if requested.
	if with_unfiltered:
		unfiltered_data_entities = copy.deepcopy(data_entities)
		for unfiltered_data_entity in unfiltered_data_entities:
			unfiltered_data_entity['label'] += '--unfiltered'

		unfiltered_aggregates = dao.get_aggregates(
				data_entities = unfiltered_data_entities,
				grouping_entities = grouping_entities,
				filters = base_filters
				)

		# Make path dicts for each tree.
		filtered_path_dict = {}
		unfiltered_path_dict = {}
		update_path_dict(aggregates, tuple(), filtered_path_dict)
		update_path_dict(unfiltered_aggregates, tuple(), unfiltered_path_dict)

		# Add unfiltered data to filtered data.
		for path, filtered_node in filtered_path_dict.items():
			unfiltered_node = unfiltered_path_dict.get(path)
			for d in unfiltered_node['data']:
				filtered_node['data'].append(d)
	

	return aggregates

# Helper function to make a dictionary of path:leaf pairs for a given tree node.
def update_path_dict(node, path, path_dict):
	cur_path = path + (node.get('id'),)

	path_dict[cur_path] = node

	if node.has_key('children'):
		for c in node['children'].values():
			update_path_dict(c, cur_path, path_dict)


