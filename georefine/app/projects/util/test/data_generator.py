import os
import csv
import fiona


def generate_project_dir(project_dir):
    generate_schema_file(project_dir)
    generate_app_config_file(project_dir)
    data_dir = os.path.join(project_dir, "data")
    os.mkdir(data_dir)
    generate_csv_data_files(data_dir)
    generate_map_layer_data_files(data_dir)

def generate_schema_file(project_dir):
    schema_file = os.path.join(project_dir, "schema.py")
    schema_fh = open(schema_file, "w")
    schema_fh.write("""
from sqlalchemy import Table, Column, ForeignKey, ForeignKeyConstraint, Integer, String, Float
from sqlalchemy.orm import relationship, mapper
from sqlalchemy import MetaData
from geoalchemy import *

tables = {}
ordered_tables = []
metadata = MetaData()

# Define tables in dependency order.
tables['test1'] = Table('test1', metadata,
		Column('id', Integer, primary_key=True),
		Column('name', String),
		)
ordered_tables.append({'id': 'test1', 'table': tables['test1']})
                    """)
    schema_fh.close()

def generate_app_config_file(project_dir):
    app_config_file = os.path.join(project_dir, "app_config.py")
    app_config_fh = open(app_config_file, "w")
    app_config_fh.write("""
                        """)
    app_config_fh.close()

def generate_csv_data_files(data_dir):
    dfiles = {}
    test1_data = []
    for i in range(3):
        test1_data.append({'id': i, 'name': "%s_name" % i})
    dfiles['test1'] = {
        'id': 'test1',
        'type': 'csv',
        'mappings': ['id', 'name'],
        'data': test1_data
    }

    for dfile in dfiles.values():
        if dfile['type'] == 'csv':
            mappings = dfile['mappings']
            for i in range(len(mappings)):
                if isinstance(mappings[i], str):
                    mappings[i] = {'source': mappings[i], 
                                   'target': mappings[i]}
            csv_file = os.path.join(data_dir, "%s.csv" % dfile['id'])
            w = csv.writer(open(csv_file, "wb"))
            w.writerow([m['target'] for m in mappings])
            for record in dfile['data']:
                w.writerow([record[m['source']] for m in mappings])

def generate_map_layer_data_files(data_dir):
    layers_dir = os.path.join(data_dir, 'map_layers')
    os.mkdir(layers_dir)
    for i in range(3):
        layer_id = "layer%s" % i
        layer_dir = os.path.join(layers_dir, layer_id)
        os.mkdir(layer_dir)

        # Write shapefile.
        shp_file = os.path.join(layer_dir, "%s.shp" % layer_id)
        c = fiona.collection(shp_file, "w", driver='ESRI Shapefile', 
                             crs={'no_defs': True, 'ellps': 'WGS84', 
                                  'datum': 'WGS84', 'proj': 'longlat'},
                             schema={
                                 'geometry': 'MultiPolygon',
                                 'properties': {
                                     'INT_ATTR': 'int',
                                     'STR_ATTR': 'str',
                                 }
                             },
                            )
        for j in range(3):
            coords = [[j, j], [j,j+1], [j+1, j+1], [j+1,j], [j,j]]
            record = {
                'id': j,
                'geometry': {
                    'type': 'MultiPolygon',
                    'coordinates': [[coords]]
                },
                'properties': {
                    'INT_ATTR': j,
                    'STR_ATTR': "str_%s" % i
                }
            }
            c.write(record)
        c.close()

        # Write SLD.
        sld_file = os.path.join(layer_dir, "%s.sld" % layer_id)
        open(sld_file, "w").write(get_sld(layer_id))

def get_sld(layer_id):
    return """
<?xml version="1.0" encoding="ISO-8859-1"?>
<StyledLayerDescriptor version="1.0.0" 
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
    xmlns="http://www.opengis.net/sld" 
    xmlns:ogc="http://www.opengis.net/ogc" 
    xmlns:xlink="http://www.w3.org/1999/xlink" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>%s</Name>
    <UserStyle>
      <Title>Simple polygon</Title>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#800080</CssParameter>
            </Fill>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
""" % layer_id
