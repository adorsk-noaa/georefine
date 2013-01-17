from georefine.app import app
from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for, jsonify, json, Response
from werkzeug import secure_filename
from jinja2 import Markup
from georefine.app import db
from georefine.app.projects.models import Project
from georefine.app.projects.util import manage_projects as projects_manage
from georefine.app.projects.util import services as projects_services
from georefine.app.keyed_strings import util as ks_util
import os
import tarfile
import hashlib
import marshal


bp = Blueprint('projects', __name__, url_prefix='/projects', template_folder='templates')

# Set default config settings if not set.
app.config.setdefault('GR_STATIC_FOLDER', app.static_folder)
app.config.setdefault('GR_PROJECTS_STATIC_FOLDER', os.path.join(
    app.config['GR_STATIC_FOLDER'], "projects"))

@app.before_first_request
def setup_projects_static_dir():
    if not os.path.exists(app.config['GR_PROJECTS_STATIC_FOLDER']):
        os.mkdir(app.config['GR_PROJECTS_STATIC_FOLDER'])

def url_for_project_static_dir(project):
    """ Get the url for a project's static dir. """
    if not app.config.get('GR_PROJECTS_STATIC_URL_PATH'):
        project_full_path = project.static_dir
        project_rel_path = project_full_path.replace(
            app.config['GR_STATIC_FOLDER'] + '/', '')
        return url_for('static', filename=project_rel_path)

def get_project(project_id):
    return db.session.query(Project).get(project_id)

@bp.route('/view/client/<int:project_id>/')
def georefine_client(project_id):
    context_root = '/' + app.config['APPLICATION_ROOT']
    project = get_project(project_id)

    georefine_config = {
        "context_root": context_root,
        "project_id": project_id,
        "project_static_dir": url_for_project_static_dir(project),
        "filter_groups": project.app_config.get('filter_groups', {}),
        "facets": project.app_config.get('facets', {}),
        "charts": project.app_config.get('charts', {}),
        "maps": project.app_config.get('maps', {}),
        "summary_bar": project.app_config.get('summary_bar', {}),
        "initial_state": project.app_config.get('initial_state', {}),
        "defaultInitialState": project.app_config.get('defaultInitialState', {}),
    }
    json_georefine_config = json.dumps(georefine_config)
    return render_template("projects/georefine_client.html", app=app, context_root=context_root, georefine_config=Markup(json_georefine_config))

@bp.route('/')
def home():
    return 'home'

@bp.route('/execute_queries/<int:project_id>/', methods=['GET', 'POST'])
def execute_queries(project_id):
    project = get_project(project_id)

    # Parse request parameters.
    query_defs= json.loads(request.args.get('QUERIES', '[]'))

    fn = projects_sevices.execute_keyed_queries
    fn_args = [project]
    fn_kwargs = {'query_defs': query_defs}
    if app.config.get('GR_PROJECTS_CACHE'):
        results = _get_cached(
            project,
            fn,
            fn_args=fn_args,
            fn_kwargs=fn_kwargs,
            key_args=['execute_queries'],
            key_kwargs=fn_args,
        )
    else:
        results = fn(*fn_args, **fn_kwargs)
    return jsonify(results=results)

@bp.route('/execute_keyed_queries//<int:project_id>/', methods=['GET', 'POST'])
def execute_keyed_queries(project_id):
    project = get_project(project_id)

    # Parse request parameters.
    key_def = json.loads(request.args.get('KEY', '{}'))
    query_defs= json.loads(request.args.get('QUERIES', '[]'))

    fn = projects_services.execute_keyed_queries
    fn_args = [project]
    fn_kwargs = {'key_def': key_def, 'query_defs': query_defs}
    if app.config.get('GR_PROJECTS_CACHE'):
        results = _get_cached(
            project,
            fn,
            fn_args=fn_args,
            fn_kwargs=fn_kwargs,
            key_args=['execute_keyed_queries'], 
            key_kwargs=fn_kwargs,
        )
    else:
        results = fn(*fn_args, **fn_kwargs)
    return jsonify(results=results)

# @TODO: Kludge to get stuff working for now, clean this up later.
@bp.route('/execute_requests/<int:project_id>/', methods=['GET', 'POST'])
def execute_requests(project_id):
    project = get_project(project_id)

    if request.method == 'POST':
        request_defs = json.loads(request.form.get('requests'), '[]')

    results = {}
    for request_def in request_defs:
        if request_def['REQUEST'] == 'execute_keyed_queries':
            fn = projects_services.execute_keyed_queries
        elif request_def['REQUEST'] == 'execute_queries':
            fn = projects_services.execute_queries
        fn_args = [project]
        fn_kwargs = request_def['PARAMETERS']
        if app.config.get('GR_PROJECTS_CACHE'):
            req_results = _get_cached(
                project,
                fn,
                fn_args=fn_args,
                fn_kwargs=fn_kwargs,
                key_args=[request_def['REQUEST']],
                key_kwargs=fn_kwargs,
            )
        else:
            req_results = fn(*fn_args, **fn_kwargs)
        results[request_def['ID']] = req_results

    return jsonify(results=results)

@bp.route('/get_map/<int:project_id>/', methods=['GET'])
def get_map(project_id):
    project = get_project(project_id)

    # Parse parameters.
    json_params = ""
    # If params key was provided, load params string.
    if request.args.get('PARAMS_KEY'):
        json_params = ks_util.getString(request.args.get('PARAMS_KEY'))

    # Parse custom parameters (overrides params key for testing purposes).
    if request.args.get('PARAMS'):
        json_params = request.args.get('PARAMS')

    params = json.loads(json_params)

    # Fix for unicode keys (py2.5 doesn't like them).
    str_params = {}
    for k,v in params.items():
        str_params[str(k).lower()] = v
    params = str_params

    wms_parameters = get_wms_parameters(request.args)

    fn = projects_services.get_data_map
    fn_args = [project]
    fn_kwargs = dict([('wms_parameters', wms_parameters)] + params.items())
    if app.config.get('GR_PROJECTS_CACHE'):
        map_image = _get_cached(
            project,
            fn,
            fn_args=fn_args,
            fn_kwargs=fn_kwargs,
            key_args=['get_data_map'],
            key_kwargs=fn_kwargs,
        )
    else:
        map_image = fn(*fn_args, **fn_kwargs)
    return Response(map_image, mimetype=wms_parameters['FORMAT'])

def get_wms_parameters(parameters):
    wms_parameters = {}
    for wms_parameter in [
        'SERVICE', 
        'VERSION', 
        'REQUEST', 
        'BBOX', 
        'FORMAT', 
        'WIDTH', 
        'HEIGHT', 
        'TRANSPARENT', 
        'SRS',
        'LAYERS'
    ]:
        value = parameters.get(wms_parameter)
        if wms_parameter == 'WIDTH' or wms_parameter == 'HEIGHT':
            value = int(value)
        wms_parameters[wms_parameter] = value
    return wms_parameters

@bp.route('/<int:project_id>/layer/<layer_id>/wms', methods=['GET'])
def layer_wms(project_id, layer_id):
    project = get_project(project_id)

    wms_parameters = get_wms_parameters(request.args)

    fn = projects_services.get_layer_map
    fn_args = [project, layer_id]
    fn_kwargs = wms_parameters
    if app.config.get('GR_PROJECTS_CACHE'):
        map_image = _get_cached(
            project,
            fn,
            fn_args=fn_args,
            fn_kwargs=fn_kwargs,
            key_args=['get_layer_map', layer_id],
            key_kwargs=fn_kwargs,
        )
    else:
        map_image = fn(*fn_args, **fn_kwargs)
    return Response(map_image, mimetype=wms_parameters['FORMAT'])

@bp.route('/colorbar/', methods=['GET'])
def get_colorbar():
    colorbar_def = json.loads(request.args.get('CBAR'))
    width = int(request.args.get('WIDTH', 100))
    height = int(request.args.get('HEIGHT', 1))
    colorbar_data = projects_services.get_colorbar(colorbar_def, width=width, height=height, format_='PNG')
    return Response(colorbar_data, mimetype='image/png')

""" Basic disk-based caching, for data which can be easily serialized. """
def _generate_cache_key(*args, **kwargs):
    s = repr(args) + repr(kwargs)
    return hashlib.md5(s).hexdigest()

def _get_cached(project, fn, fn_args=[], fn_kwargs={}, key_args=[],
                key_kwargs={}):
    cache_dir = _get_cache_dir(project)
    serialized_args = ''.join([repr(a) for a in [key_args, key_kwargs]])
    key = hashlib.md5(serialized_args).hexdigest()
    key_path = os.path.join(cache_dir, key)
    # Cache if not already cached..
    if not os.path.exists(key_path):
        print "cache miss"
        with open(key_path, 'wb') as f:
            result = fn(*fn_args, **fn_kwargs)
            marshal.dump(result, f)
        return result
    # Otherwise return from cache.
    print "cache hit"
    with open(key_path, 'rb') as f:
        return marshal.load(f)

def _get_cache_dir(project):
    cache_dir_path = os.path.join(project.data_dir, 'cache')
    if not os.path.exists(cache_dir_path):
        os.makedirs(cache_dir_path)
    return cache_dir_path
