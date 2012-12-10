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

if __name__ == "__main__":
    unittest.main()
