import tempfile
from jinja2 import Environment, PackageLoader
import os
import csv
import fiona
import tarfile
import json
import shutil
import georefine.util.mapping.sld_util as sld_util


template_env = Environment(
    loader=PackageLoader(
        'georefine.app.projects.util', 
        'templates'
    )
)


def generate_source_defs():
    return [
        {
            'id':  'Src1',
            'cols': [
                {
                    'name': 'id',
                    'type_': 'Integer',
                    'kwargs': {
                        'primary_key': True,
                    },
                    'data': lambda n, r, d: None,
                },
                {
                    'name': 'float_',
                    'type_': 'Float',
                    'data': lambda n, r, d: float(n),
                },
                {
                    'class': 'GeometryExtensionColumn',
                    'name': 'geom',
                    'type_': 'MultiPolygon(2)',
                    'csv_name': 'geom_wkt',
                    'data': generate_multipolygon_wkt_for_record,
                },
            ],
            'GeometryDDL': True,
        },

        {
            'id':  'Src2',
            'cols': [
                {
                    'name': 'id',
                    'type_': 'Integer',
                    'kwargs': {
                        'primary_key': True,
                    },
                    'data': lambda n, r, d: None,
                },
                {
                    'name': 'float_',
                    'type_': 'Float',
                    'data': lambda n, r, d: float(n),
                },
                {
                    'name': 'src1_id',
                    'type_': 'Integer',
                    'args': [
                        'ForeignKey("Src1.id")',
                    ],
                    'data': lambda n, r, d: d['Src1'][n]['id'],
                },
            ],
            'GeometryDDL': True,
        }]

def generate_sources(source_defs=None):
    if not source_defs:
        source_defs = generate_source_defs()

    sources = []

    for source_def in source_defs:
        source = {
            'id': source_def['id'],
            'cols': source_def['cols'],
            'col_strs': get_col_strs_for_source_def(source_def),
            'data': get_data_for_source_def(source_def),
            'GeometryDDL': source_def.get('GeometryDDL'),
        }
        sources.append(source)

    return sources

def get_col_strs_for_source_def(source_def):
    col_strs = []
    for col in source_def['cols']:
        args = col.get('args', [])
        args.insert(0, col['type_'])
        args.insert(0, "'%s'" % col['name'])
        args_str = ','.join(args)
        kwargs_str = ','.join(["%s=%s" % (k,v) 
                               for k, v in col.get('kwargs', {}).items()])
        combined_args_str = args_str + ',' + kwargs_str
        class_str = col.get('class', 'Column')
        col_str = "%s(%s)" % (class_str, combined_args_str)
        col_strs.append(col_str)
    return col_strs

def get_data_for_source_def(source_def, n=10, data={}):
    records = []
    for i in range(n):
        record = {}
        for col in source_def['cols']:
            if col.get('data'):
                value = col['data'](i, record, data)
            else:
                value = None
            record[col['name']] = value
        records.append(record)

    data[source_def['id']] = records

    return records

def generate_polygon_coords(x=0, dx=1, y=0, dy=1):
    coords = [[x, y], [x, y+dy], [x+dx, y+dy], [x+dx, y], [x, y]]
    return coords

def generate_multipolygon_wkt_for_record(n, record=None, data={}, **kwargs):
    """ Generate a multipolygon for a data record. """
    return generate_multipolygon_wkt(x=n, y=n)

def generate_multipolygon_wkt(**kwargs):
    coords = generate_polygon_coords(**kwargs)
    wkt = "MULTIPOLYGON(((%s)))" % (','.join(["%s %s" % (c[0], c[1]) for c in coords]))
    return wkt

def generate_schema(target_file=None, sources=[]):
    """ Generate schema file. """
    if not target_file:
        hndl, target_file = tempfile.mkstemp("gr.project.schema.")

    schema_fh = open(target_file, "wb")
    schema_template = template_env.get_template('schema.py')
    schema_fh.write(schema_template.render(sources=sources))
    schema_fh.close()
    return target_file

def generate_app_config(target_file=None):
    """ Generate app_config file. """
    if not target_file:
        hndl, target_file = tempfile.mkstemp("gr.project.app_config.")
    app_config_fh = open(target_file, "wb")
    app_config_template = template_env.get_template('app_config.py')
    app_config_fh.write(app_config_template.render())
    app_config_fh.close()
    return target_file

def generate_layers(target_dir=None, layer_defs=None, n=3):
    if not target_dir:
        target_dir = tempfile.mkdtemp(prefix='layers.')

    if not layer_defs:
        layer_defs = []
        for i in range(n):
            layer_defs.append(generate_layer_def(layer_id="layer_%s" % i, n=10))

    for layer_def in layer_defs:
        layer_dir = os.path.join(target_dir, layer_def['id'])
        os.makedirs(layer_dir)
        generate_layer(target_dir=layer_dir, layer_def=layer_def)

def generate_layer(target_dir=None, layer_def=None):
    if not layer_def:
        layer_def = generate_layer_def()

    if not target_dir:
        target_dir = tempfile.mkdtemp(prefix="%s." % layer_def['id'])

    shp_file = os.path.join(target_dir, layer_def['shpfile_filename'])
    shp_writer = fiona.collection(
        shp_file, "w", driver="ESRI Shapefile", schema=layer_def['schema'], 
        crs=layer_def['crs'],
    )
    for record in layer_def['records']:
        shp_writer.write(record)
    shp_writer.close()

    mfile_def = layer_def.get('mapfile_def')
    if mfile_def:
        mfile_file = os.path.join(target_dir, mfile_def['filename'])
        open(mfile_file, "wb").write(mfile_def['content'])

    metadata_file = os.path.join(target_dir, "metadata.json")
    open(metadata_file, "wb").write(json.dumps(layer_def['metadata']))

    return target_dir


def generate_layer_def(layer_id='layer', properties=None, n=10):
    if not properties:
        properties = {
            'VALUE': 'float'
        }

    layer_def = {
        'id': layer_id, 
        'crs': {'+init': 'epsg:4326'},
        'schema': {
            'geometry': 'MultiPolygon',
            'properties': properties,
        },
        'records': [],
        'mapfile_filename': '%s.map' % layer_id,
        'shpfile_filename': '%s.shp' % layer_id,
    }

    layer_def['metadata'] = {
        'mapfile': layer_def['mapfile_filename'],
    }

    layer_def['mapfile_def'] = {
        'filename': layer_def['mapfile_filename'],
        'content': template_env.get_template('mapfile.map').render(
            layer_def=layer_def),
    }

    data = []
    for i in range(n):
        coords = generate_polygon_coords(x=i, y=i)
        record = {
            'geometry': {
                'type': layer_def['schema']['geometry'],
                'coordinates': [[coords]],
            },
            'id': i,
            'properties': {},
        }
        geom = generate_multipolygon_wkt(i, x=i, y=i)
        for prop, type_ in layer_def['schema']['properties'].items():
            record['properties'][prop] = eval(type_)(i)
        layer_def['records'].append(record)

    return layer_def

def generate_project_file(target_file=None, rmdir=True, **kwargs):
    """ Generate a project dir. """
    project_dir = generate_project_dir(**kwargs)
    if not target_file:
        target_file = project_dir + '.tar.gz'
    tar = tarfile.open(target_file, "w:gz")
    for item in os.listdir(project_dir):
        path = os.path.join(project_dir, item)
        tar.add(path, arcname=item)
    tar.close()
    if rmdir:
        shutil.rmtree(project_dir)
    return target_file

def generate_project_dir(target_dir=None, source_defs=None,):
    """ Generate a project file. """
    if not target_dir:
        target_dir = tempfile.mkdtemp(prefix="gr.project.")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Create mock sources.
    sources = generate_sources(source_defs=source_defs)

    # Create mock schema.
    schema_file = os.path.join(target_dir, 'schema.py')
    generate_schema(target_file=schema_file, sources=sources)

    # Create mock data per the schema.
    data_dir = os.path.join(target_dir, 'data')
    os.makedirs(data_dir)
    for source in sources:
        csv_file = os.path.join(data_dir, source['id'] + '.csv')
        writer = csv.writer(open(csv_file, 'wb'))
        col_names = []
        for col in source['cols']:
            col_names.append(col.get('csv_name', col['name']))
        writer.writerow(col_names)
        for record in source['data']:
            writer.writerow([record[col['name']] for col in source['cols']])

    # Create mock layers.
    layers_dir = os.path.join(target_dir, 'layers')
    generate_layers(target_dir=layers_dir)

    # Cretae mock app config.
    app_config_file = os.path.join(target_dir, 'app_config.py')
    generate_app_config(target_file=app_config_file)

    return target_dir
