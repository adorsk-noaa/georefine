from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
import georefine.flask_config as flask_config
import os

app = Flask(__name__)
app.config.from_object(flask_config)

db = SQLAlchemy(app)

@app.errorhandler(404)
def not_found(error):
	return 'badness', 404

from georefine.app.projects.views import bp as projects_bp
app.register_blueprint(projects_bp)
