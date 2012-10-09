from georefine.app import db as db
from georefine.config import config

from flask import Flask, render_template, escape
from flask_admin import Admin

import os


app = Flask(__name__)
app.config.from_object(config)
app.config.from_pyfile(os.path.join(app.instance_path, 'app_config.py'),
                       silent=True)

admin = Admin(app)

@app.errorhandler(404)
def not_found(error):
	return 'badness', 404

@app.teardown_request
def shutdown_session(exception=None):
	db.session.remove()


from .login import login_manager
from flask_login import current_user

@app.route('/')
def index():
    return "da index, current user is: '%s'" % escape(str(current_user))

from georefine.app.projects.admin import ProjectsAdmin
admin.add_view(ProjectsAdmin(db.session))

from georefine.app.projects.views import bp as projects_bp
app.register_blueprint(projects_bp)

from georefine.app.keyed_strings.views import bp as keyed_strings_bp
app.register_blueprint(keyed_strings_bp)
