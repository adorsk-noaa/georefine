import unittest
import georefine.app as gr

class ProjectsTest(unittest.TestCase):

	def setUp(self):
		gr.app.config['TESTING'] = True
		self.app = gr.app.test_client()

	def test_test_facets(self):
		r = self.app.get('/projects/test_facets/1/', data=dict(), follow_redirects=True)
		print r.data
	
if __name__ == '__main__':
	unittest.main()
