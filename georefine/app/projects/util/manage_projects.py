from ..models import Project
from app import db
import os
import imp

def create_project(project): 
	# Load project schema from project dir.
	schema_file = os.path.join(project.dir, 'schema.py')
	schema = imp.load_source("gr_project_schema", schema_file)

	print schema



