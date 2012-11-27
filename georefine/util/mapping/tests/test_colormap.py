import unittest
from georefine.util.mapping import colormap as cmap


class ColorMapTestCase(unittest.TestCase):
    def test_generate_bw_colormap(self):
        bw_colormap = cmap.generate_hsl_bw_colormap()

    def test_get_mapped_color(self):
        vmin = 0
        vmax = 10
        bw_colormap = cmap.generate_hsl_bw_colormap(vmin=vmin, vmax=vmax)
        mapped_hsls = []
        expected_hsls = []
        n = 10
        for v in range(n):
            mapped_hsls.append(cmap.get_mapped_color(v, bw_colormap))
            expected_hsls.append({'h': 0, 's': 1, 'l': float(v)/n})
        self.assertEquals(mapped_hsls, expected_hsls)

if __name__ == "__main__":
    unittest.main()
