from georefine.app import app
from georefine.config import config as gr_conf
from flask import Blueprint, request, redirect, render_template, flash, g, session, url_for, jsonify, json, Response
from werkzeug import secure_filename
from jinja2 import Markup
from georefine.app import db
from georefine.app.projects.forms import CreateProjectForm
from georefine.app.projects.models import Project, MapLayer
from georefine.app.projects.util import manage_projects as projects_manage
from georefine.app.projects.util import services as projects_services
from georefine.app.projects.util import layer_services as layer_services
from georefine.app.keyed_strings import util as ks_util
import os
import tarfile

bp = Blueprint('projects', __name__, url_prefix='/projects', template_folder='templates')
context_root = "/%s" % app.config['APPLICATION_ROOT']
geoserver_url = "/geoserver"

def get_project(project_id):
    return db.session.query(Project).get(project_id)

@bp.route('/view/client/<int:project_id>/')
def georefine_client(project_id):
    project = get_project(project_id)
    project.app_config = projects_manage.getProjectAppConfig(project)
    georefine_config = {
        "context_root": context_root,
        "geoserver_url": geoserver_url,
        "project_id": project_id,
        "filter_groups": project.app_config.get('filter_groups', {}),
        "facets": project.app_config.get('facets', {}),
        "charts": project.app_config.get('charts', {}),
        "maps": project.app_config.get('maps', {}),
        "summary_bar": project.app_config.get('summary_bar', {}),
        "initial_state": project.app_config.get('initial_state', {}),
        "defaultInitialState": project.app_config.get('defaultInitialState', {}),
    }
    json_georefine_config = json.dumps(georefine_config)
    return render_template("projects/georefine_client.html", context_root=context_root, georefine_config=Markup(json_georefine_config))

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
            return "file is: {}, project is: {}".format(filename, project.id)
    else:
        flash('bad file')
    
    return render_template("projects/create_project.html", form=form)

@bp.route('/execute_queries/<int:project_id>/', methods=['GET', 'POST'])
def execute_queries(project_id):
    project = get_project(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    query_defs= json.loads(request.args.get('QUERIES', '[]'))

    results = projects_services.execute_keyed_queries(
            project = project,
            query_defs = query_defs
            )

    return jsonify(results=results)

@bp.route('/execute_keyed_queries//<int:project_id>/', methods=['GET', 'POST'])
def execute_keyed_queries(project_id):
    project = get_project(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    # Parse request parameters.
    key_def = json.loads(request.args.get('KEY', '{}'))
    query_defs= json.loads(request.args.get('QUERIES', '[]'))

    results = projects_services.execute_keyed_queries(
            project = project,
            key_def=key_def,
            query_defs = query_defs
            )

    return jsonify(results=results)


# @TODO: Kludge to get stuff working for now, clean this up later.
@bp.route('/execute_requests/<int:project_id>/', methods=['GET', 'POST'])
def execute_requests(project_id):
    project = get_project(project_id)
    project.schema = projects_manage.getProjectSchema(project)

    if request.method == 'POST':
        request_defs = json.loads(request.form.get('requests'), '[]')

    results = {}
    for request_def in request_defs:
        if request_def['REQUEST'] == 'execute_keyed_queries':
            results[request_def['ID']] = projects_services.execute_keyed_queries(
                    project = project,
                    **request_def['PARAMETERS']
                    )

        elif request_def['REQUEST'] == 'execute_queries':
            results[request_def['ID']] = projects_services.execute_queries(
                    project = project,
                    **request_def['PARAMETERS']) 

    return jsonify(results=results)
            


@bp.route('/get_map/<int:project_id>/', methods=['GET'])
def get_map(project_id):
    project = get_project(project_id)
    project.schema = projects_manage.getProjectSchema(project)

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
        str_params[str(k)] = v
    params = str_params

    # Parse WMS parameters.
    wms_parameters = get_wms_parameters(request.args)

    map_image = projects_services.get_map(
            project, 
            MAP_PARAMETERS=wms_parameters,
            **params
            )
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

def get_layer(layer_id):
    return db.session.query(MapLayer).filter(
        MapLayer.layer_id == layer_id).one()

@bp.route('/layer/<layer_id>/wms', methods=['GET'])
def layer_wms(layer_id):
    layer = get_layer(layer_id)
    wms_parameters = get_wms_parameters(request.args)
    map_image = layer_services.get_map(
        layer=layer,
        wms_parameters=wms_parameters
    )
    return Response(map_image, mimetype=wms_parameters['FORMAT'])
