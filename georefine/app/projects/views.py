from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for
from werkzeug import secure_filename
from app import db
from app.projects.forms import CreateProjectForm
from app.projects.models import Project
import os


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

		project_file = request.files['project_file']
		if project_file:
			print "pf is: ", project_file
			filename = secure_filename(project_file.filename)
			project_file.save(os.path.join('/tmp/', filename))
			return "file is: {}".format(filename)
	else:
		flash('bad file')
	
	return render_template("projects/create_project.html", form=form)

