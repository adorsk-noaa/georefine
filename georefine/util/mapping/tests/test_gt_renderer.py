import unittest
from georefine.util.mapping.gt_renderer import GeoToolsMapRenderer

class GeoToolsMapRendererTest(unittest.TestCase):

	def testRendering(self):
		renderer = GeoToolsMapRenderer()

		renderer.renderMap()

if __name__ == '__main__':
	unittest.main()
