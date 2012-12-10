import unittest
from georefine.util.mapping import interpolate as interpolate


class InterpolateTestCase(unittest.TestCase):
    def test_lin_interpolate(self):
        xs = [-1.5]
        curve = [(-2, -100), (2, 100)]
        self.assertEquals(
            interpolate.lin_interpolate(xs, curve),
            [(-1.5, -75.0)]
        )

if __name__ == '__main__':
    unittest.main()
