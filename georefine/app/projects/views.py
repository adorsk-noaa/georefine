from georefine.config import config as gr_conf
from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for, jsonify, json, Response
from werkzeug import secure_filename
from jinja2 import Markup
from georefine.app import db
from georefine.app.projects.forms import CreateProjectForm
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as projects_manage
from georefine.app.projects.util import services as projects_services
import os
import tarfile

bp = Blueprint('projects', __name__, url_prefix='/projects', template_folder='templates')

@bp.before_request
def before_request():
	g.project = None
	if 'project_id' in session:
		g.project = Project.query.get(session['project_id'])

@bp.route('/test_facets/<int:project_id>/')
def test_facets(project_id):
	project = Project.query.get(project_id)
	project.app_config = projects_manage.getProjectAppConfig(project)
	json_facets = json.dumps(project.app_config.facets)
	return render_template("projects/test_facets.html", project_id=project.id, facets=Markup(json_facets))

@bp.route('/test_charts/<int:project_id>/')
def test_charts(project_id):
	project = Project.query.get(project_id)
	project.app_config = projects_manage.getProjectAppConfig(project)
	json_charts = json.dumps(project.app_config.charts)
	return render_template("projects/test_charts.html", project_id=project.id, charts=Markup(json_charts))

@bp.route('/')
def home():
	return 'home'

@bp.route('/create_project/', methods=['GET', 'POST'])
def create_project():
	form = CreateProjectForm(request.form)
	if form.validate_on_submit():
		project = Project(name=form.name.data)

		# Create a directory for the project.
		# @TODO: change this to use project id or uuid later.
		project_dir = os.path.join(gr_conf['PROJECT_FILES_DIR'], project.name)
		os.mkdir(project_dir)

		project.dir = project_dir
		db.session.add(project)
		db.session.commit()

		project_file = request.files['project_file']
		if project_file:
			filename = secure_filename(project_file.filename)

			# HACK.
			# @TODO: fix this later.
			tmp_filename = os.path.join('/tmp', filename)
			project_file.save(tmp_filename)

			# Unpack the project file to the project dir.
			tar = tarfile.open(tmp_filename)
			tar.extractall(project_dir)
			tar.close()
			return "file is: {}".format(filename)
	else:
		flash('bad file')
	
	return render_template("projects/create_project.html", form=form)

@bp.route('/get_aggregates/<int:project_id>/', methods=['GET', 'POST'])
def get_aggregates(project_id):
	project = Project.query.get(project_id)
	project.schema = projects_manage.getProjectSchema(project)

	# Parse request parameters.
	data_entities = json.loads(request.args.get('data_entities', '[]'))
	grouping_entities = json.loads(request.args.get('grouping_entities', '[]'))
	filters = json.loads(request.args.get('filters', '[]'))
	with_unfiltered = json.loads(request.args.get('with_unfiltered', 'false'))
	base_filters = json.loads(request.args.get('base_filters', '[]'))

	result = projects_services.get_aggregates(
			project, 
			data_entities = data_entities, 
			grouping_entities = grouping_entities, 
			filters = filters,
			with_unfiltered = with_unfiltered,
			base_filters = base_filters
			)
	return jsonify(result)

@bp.route('/get_map/<int:project_id>/', methods=['GET'])
def get_map(project_id):
	project = Project.query.get(project_id)
	project.schema = projects_manage.getProjectSchema(project)

	# Parse request parameters.

	map_image = projects_services.get_map(project)
	return Response(map_image, mimetype='image/gif')

