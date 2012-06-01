from flask import Flask, render_template
import georefine.flask_config as flask_config
from georefine.app import db
import os

app = Flask(__name__)
app.config.from_object(flask_config)

@app.errorhandler(404)
def not_found(error):
	return 'badness', 404

@app.teardown_request
def shutdown_session(exception=None):
	db.session.remove()

from georefine.app.projects.views import bp as projects_bp
app.register_blueprint(projects_bp)
