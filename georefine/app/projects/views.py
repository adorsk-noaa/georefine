from georefine.config import config as gr_conf
from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for
from werkzeug import secure_filename
from georefine.app import db
from georefine.app.projects.forms import CreateProjectForm
from georefine.app.projects.models import Project
import os
import tarfile

bp = Blueprint('projects', __name__, url_prefix='/projects', template_folder='templates')

@bp.before_request
def before_request():
	g.project = None
	if 'project_id' in session:
		g.project = Project.query.get(session['project_id'])

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

