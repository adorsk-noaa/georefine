from georefine import config

from flask import Flask, render_template, escape

import os
import imp


# Import instance config if it exists before app is created, in order to get
# static dirs.
this_dir = os.path.dirname(os.path.abspath(__file__))
instance_config_filename = os.path.join(this_dir, 'instance', 'app_config.py')
instance_config = imp.new_module('instance_config')
instance_config.__file__ = instance_config_filename
try:
    execfile(instance_config_filename, instance_config.__dict__)
except IOError, e:
    pass

app_kwargs = {}
app_attrs = ['static_folder', 'static_url_path']
for attr in app_attrs:
    uc_attr = attr.upper()
    value = getattr(instance_config, uc_attr, None) \
            or getattr(config, uc_attr, None)
    if value is not None:
        app_kwargs[attr] = value

# Initialize app.
app = Flask(__name__, instance_path=os.path.join(this_dir, 'instance'), 
            **app_kwargs)

# Setup app config.
app.config.from_object(config)
app.config.from_object(instance_config)

import db

@app.errorhandler(404)
def not_found(error):
	return 'badness', 404

@app.teardown_request
def shutdown_session(exception=None):
	db.session.remove()

@app.after_request
def after(response):
    if app.config.get('ALLOW_ORIGIN'):
        response.headers.add('Access-Control-Allow-Origin',
                             app.config.get('ALLOW_ORIGIN'))
    return response

from georefine.app.projects.views import bp as projects_bp
app.register_blueprint(projects_bp)

from georefine.app.keyed_strings.views import bp as keyed_strings_bp
app.register_blueprint(keyed_strings_bp)
