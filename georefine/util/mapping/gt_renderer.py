import os
import sys
import java.lang

from java.io import File as JFile
from org.geotools.data import FileDataStoreFinder
from org.geotools.data.simple import SimpleFeatureSource
from org.geotools.map import DefaultMapContext
from org.geotools.swing import JMapFrame
from org.geotools.renderer.lite import StreamingRenderer
from java.awt.image import BufferedImage
from java.awt import Rectangle
from java.awt import Color
from java.io import ByteArrayOutputStream
from javax.imageio import ImageIO
from org.python.core.util import StringUtil
from StringIO import StringIO
from org.python.core import Py


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

		"""
		print "gt map is: ", gt_map
		JMapFrame.showMap(gt_map)
		raw_input("foo")
		"""

		gt_renderer = StreamingRenderer()
		gt_renderer.setMapContent(gt_map)

		image_bounds = Rectangle(0, 0, 400, 400)

		buffered_image = BufferedImage(image_bounds.width, image_bounds.height, BufferedImage.TYPE_INT_RGB)
		graphics = buffered_image.createGraphics()
		graphics.setPaint(Color.WHITE)
		graphics.fill(image_bounds)

		gt_renderer.paint(graphics, image_bounds, gt_map.getMaxBounds())
		byte_array_output_stream = ByteArrayOutputStream()
		ImageIO.write(buffered_image, "jpg", byte_array_output_stream)
		byte_array = byte_array_output_stream.toByteArray()

		raw_image = Py.newString(StringUtil.fromBytes(byte_array))

		"""
		gt_map = DefaultMapContext()

		for layer in map_context.get('layers', []):
			data_store = layer.get('data_store')
			style = layer.get('style')
			gt_map.addLayer(feature_source, style)

		"""

		



