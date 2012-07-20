from flask import Flask, render_template
import georefine.flask_config as flask_config
import db
import os
import logging
from georefine.config import config as gr_config

app = Flask(__name__)
app.config.from_object(flask_config)

file_handler = logging.FileHandler(gr_config['LOGFILE'])
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
app.logger.addHandler(file_handler) 

@app.errorhandler(404)
def not_found(error):
	return 'badness', 404

@app.teardown_request
def shutdown_session(exception=None):
	db.session.remove()

from georefine.app.projects.views import bp as projects_bp
app.register_blueprint(projects_bp)

from georefine.app.keyed_strings.views import bp as keyed_strings_bp
app.register_blueprint(keyed_strings_bp)
