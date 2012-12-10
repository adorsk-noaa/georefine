import unittest
from georefine.util.mapping import colormap as cmap


class ColorMapTestCase(unittest.TestCase):
    def test_generate_bw_colormap(self):
        bw_colormap = cmap.generate_hsv_bw_colormap()

    def test_get_mapped_color(self):
        vmin = 0
        vmax = 10
        bw_colormap = cmap.generate_hsv_bw_colormap(vmin=vmin, vmax=vmax)
        mapped_hsvs = []
        expected_hsvs = []
        n = 10
        for v in range(n):
            mapped_hsvs.append(cmap.get_mapped_color(v, bw_colormap))
            expected_hsvs.append({'h': 0, 's': 1, 'l': float(v)/n})
        self.assertEquals(mapped_hsvs, expected_hsvs)

    def test_generate_bins(self):
        vmin = 0
        vmax = 4
        num_bins = 4

        # Simple generation.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins),
            [(0,1,), (1,2,), (2,3,),(3,4,)]
        )

        # include_bins.
        # Middle
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(1.5,2.5,)]),
            [(0,1,), (1,1.5,), (1.5, 2.5,), (2.5,3,),(3,4,)]
        )
        # Off left edge.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(-2,-1,)]),
            [(-2,-1,), (0,1,), (1,2), (2,3), (3,4,)]
        )
        # Off right edge.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(5,6,)]),
            [(0,1,), (1,2), (2,3), (3,4,), (5,6,)]
        )
        # Spanning left edge.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(-.5,.5,)]),
            [(-.5, .5,),(.5,1,), (1,2), (2,3), (3,4,)]
        )

        # Spanning right edge.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(3.5,4.5,)]),
            [(0, 1,), (1,2), (2,3), (3,3.5,), (3.5, 4.5,)]
        )

        # Spanning both edges.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(-.5,4.5,)]),
            [(-.5, 4.5,)]
        )

        # Multiple.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(.5,1.5,), (2.5, 3.5)]),
            [(0,.5,), (.5,1.5,), (1.5, 2,), (2, 2.5,),(2.5, 3.5,), (3.5,4,)]
        )

        # Include values.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_values=[2],
                               value_bin_pct_width=.2),
            [(0,1), (1,1.9), (1.9, 2.1), (2.1,3), (3,4)]
        )

        # Include bins and values.
        self.assertEquals(
            cmap.generate_bins(vmin=vmin, vmax=vmax, num_bins=num_bins,
                               include_bins=[(1.5, 2.5)],
                               include_values=[2],
                               value_bin_pct_width=.2),
            [(0,1), (1,1.5), (1.5, 1.9), (1.9, 2.1), (2.1, 2.5), (2.5, 3),
             (3,4)]
        )

    def test_generate_colored_bins(self):
        test_cmap = dict(
            zip(
                ['c1'],
                [ [(-2, -100), (2,100)] ]
            )
        )

        self.assertEquals(
            cmap.generate_colored_bins(colormap=test_cmap, vmin=-2, vmax=2, 
                                       num_bins=4, include_bins=[(-.5, .5)]),
            [
                ((-2, -1), {'c1': -75}),
                ((-1, -.5), {'c1': -37.5}),
                ((-.5, .5), {'c1': 0}),
                ((.5, 1), {'c1': 37.5}),
                ((1, 2), {'c1': 75}),
            ]
        )

    def test_generate_colorbar_img(self):
        test_cmap = dict(
            zip(
                ['r', 'g', 'b'],
                [[(0,0), (1,200)]] * 3
            )
        )

        width = 100
        height = 100
        
        img = cmap.generate_colorbar_img(
            width=100, height=100, colormap=test_cmap, vmin=0, vmax=1, 
            num_bins=4)

        from PIL import Image, ImageDraw
        expected_img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(expected_img)
        expected_rects = [
            [0,25,(25,25,25)],
            [25,50,(75,75,75)],
            [50,75,(125,125,125)],
            [75,100,(175,175,175)],
        ]
        for r in expected_rects:
            draw.rectangle([(r[0], 0), (r[1], height)], fill=r[2])
        self.assertEquals(img.tostring(), expected_img.tostring())

    def test_convert_color(self):
        rgb_c = {'r': 128, 'g': 128, 'b': 128}
        hsv_c = {'h': 0, 's': 0, 'v': 128}
        hls_c = {'h': 0, 's': 0, 'l': 128}

        # rgb <-> hsv
        self.assertEquals(
            cmap.convert_color(rgb_c, to_schema='hsv'),
            hsv_c,
        )
        self.assertEquals(
            cmap.convert_color(hsv_c, to_schema='rgb'),
            rgb_c
        )

        # rgb <-> hls
        self.assertEquals(
            cmap.convert_color(rgb_c, to_schema='hls'),
            hls_c
        )
        self.assertEquals(
            cmap.convert_color(hls_c, to_schema='rgb'),
            rgb_c
        )

if __name__ == "__main__":
    unittest.main()
