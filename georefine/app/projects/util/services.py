from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects
from georefine.util.sa.sa_dao import SA_DAO

def get_dao(project):
	schema = manage_projects.get_project_schema(project)
	return SA_DAO(session=db.session, primary_class=schema.primary_class)

def get_entities(project):
	dao = get_dao(project)
	return dao.get_entities()

def get_aggregates(project):
	schema = manage_projects.get_project_schema(project)
	dao = get_dao(schema)


