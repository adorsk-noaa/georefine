import unittest
import georefine.app as gr
from flask import json

class ProjectsTest(unittest.TestCase):

    def setUp(self):
        gr.app.config['TESTING'] = True
        self.app = gr.app.test_client()
        self.base_path = '/ks'

    def test_getKey(self):
        data = {"s" : "asdfasdfasdfasdf"}
        r = self.app.post(self.base_path + '/getKey/', data=data) 

    def test_getString(self):
        data = {"s" : "asdfasdfasdfasdf" }
        r = self.app.post(self.base_path + '/getKey/', data=data) 
        key = json.loads(r.data).get('key')
        path = self.base_path + "/getString/" + key
        r = self.app.get(path, follow_redirects=True)

if __name__ == '__main__':
    unittest.main()
