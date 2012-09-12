import unittest
import sys
import georefine.util.mapping.sld_util as sld_util


class SLDTest(unittest.TestCase):

    def test_get_polygon_gradient_sld(self):
        num_classes = 3
        classes = [[None, 0]]
        for i in range(num_classes):
            classes.append([i, i+1])
        classes.append([num_classes, None])
        print sld_util.get_polygon_gradient_sld(
            layer_name="test", 
            value_attr="value", 
            classes=classes
        )

if __name__ == '__main__':
    unittest.main()
