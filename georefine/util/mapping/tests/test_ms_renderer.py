import unittest
import sys
from georefine.util.mapping.ms_renderer import MapScriptRenderer


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

        img = renderer.renderLayers(
            mapfile="/home/adorsk/t/test.map",
            wms_parameters=wms_parameters,
            layers=layers
        )
        print img

if __name__ == '__main__':
    unittest.main()
