import unittest
import georefine.app as gr

class ProjectsTest(unittest.TestCase):

    def setUp(self):
        gr.app.config['TESTING'] = True
        self.app = gr.app.test_client()
        self.base_path = '/ks'

    def test_getKey(self):
        data = { 
                "s" : "asdfasdfasdfasdf"
                }
        r = self.app.post(self.base_path + '/getKey/', data=data) 
        print r.data

    def test_getString(self):
        key = "asdfasdfasdfasdf"
        path = self.base_path + "/getString/" + key
        r = self.app.get(path, follow_redirects=True)
        print r.data

if __name__ == '__main__':
    unittest.main()
