from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.sa.sa_dao import SA_DAO

def get_dao(project):
	return SA_DAO(session=db.session, primary_class=project.schema.primary_class)

def get_entities(project):
	dao = get_dao(project)
	return dao.get_entities()

def get_aggregates(project, data_entities=[], grouping_entities=[], filters=[]):
	dao = get_dao(project)
	return dao.get_aggregates(data_entities=data_entities, grouping_entities=grouping_entities, filters=filters)

def get_map(project):
	dao = get_dao(project)
	return open('/data/burger.png').read()
	# @TODO: dummy return for right now.	




