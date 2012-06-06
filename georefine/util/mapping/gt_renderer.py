import os

from java.io import File as JFile
from org.geotools.data import FileDataStoreFinder
from org.geotools.data.simple import SimpleFeatureSource
from org.geotools.map import DefaultMapContext
from org.geotools.swing import JMapFrame
from org.geotools.renderer.lite import StreamingRenderer

class GeoToolsMapRenderer(object):

	def __init__(self):
		pass

	def renderMap(map_context=None):

		map_file = "%s/tests/test_gis_data/ne_110m_admin_1_states_provinces_shp.shp" % os.path.dirname(__file__)
		data_file = JFile(map_file)

		data_store = FileDataStoreFinder.getDataStore(data_file)
		feature_source = data_store.getFeatureSource()

		gt_map = DefaultMapContext()
		gt_map.setTitle('foo')
		gt_map.addLayer(feature_source, None)

		print "gt map is: ", gt_map
		JMapFrame.showMap(gt_map)
		raw_input("foo")

		"""
		gt_map = DefaultMapContext()

		for layer in map_context.get('layers', []):
			data_store = layer.get('data_store')
			style = layer.get('style')
			gt_map.addLayer(feature_source, style)

		"""

		



