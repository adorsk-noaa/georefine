import unittest
import sys
from georefine.util.mapping.ms_renderer import MapScriptRenderer
from PIL import Image
from cStringIO import StringIO



class MapScriptRendererTest(unittest.TestCase):

    def testGetMapObj(self):
        renderer = MapScriptRenderer()
        mapObj = renderer.get_mapObj()
        assert mapObj.__class__.__name__ == 'mapObj'

    def testRendering(self):
        renderer = MapScriptRenderer()

        layers = [
            {
                'name': 'layer1',
                'connection': 'host=localhost password=test dbname=gis_test user=test',
                'connectiontype': 'POSTGIS',
                'data': 'geom FROM world_borders USING UNIQUE gid USING srid=4326',
                'projection': 'init=epsg:4326',
                'type': 'POLYGON',
                'sld': {
                    'doc': self.get_sld(),
                    'stylelayer': 'foo'
                }
            }
        ]

        wms_parameters = {
                'SERVICE': 'WMS' ,
                'VERSION': '1.1.0', 
                'REQUEST': 'GetMap', 
                'LAYERS': ','.join([l['name'] for l in layers]),
                'SRS':'EPSG:4326',
                'BBOX':'-180.0,-90.0,180.0,90.0',
                'FORMAT':'image/gif',
                'WIDTH':'640',
                'HEIGHT':'640',
                }

        imgObj = renderer.renderLayers(
            wms_parameters=wms_parameters,
            layers=layers
        )
        assert imgObj.__class__.__name__ == 'imageObj'

        im = Image.open(StringIO(renderer.imgObj_to_bytes(imgObj))).show()

    def get_sld(self):
        return """<?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor version="1.0.0" 
        xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd" 
        xmlns="http://www.opengis.net/sld" 
        xmlns:ogc="http://www.opengis.net/ogc" 
        xmlns:xlink="http://www.w3.org/1999/xlink" 
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <NamedLayer>
        <Name>foo</Name>
        <UserStyle>
          <Title>SLD Cook Book: Simple polygon</Title>
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
    """

if __name__ == '__main__':
    unittest.main()
