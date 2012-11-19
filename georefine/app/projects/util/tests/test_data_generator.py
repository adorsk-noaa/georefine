import unittest
import georefine.app.projects.util.data_generator as dg


class DataGeneratorTest(unittest.TestCase):
    def test_generate_sources(self):
        source_defs = dg.generate_sources()

    def test_generate_layer_def(self):
        ld = dg.generate_layer_def()

    def test_generate_layer(self):
        ld = dg.generate_layer()
    
    def test_generate_project_file(self):
        pf = dg.generate_project_file()
        print pf

if __name__ == '__main__':
    unittest.main()
