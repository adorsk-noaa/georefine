import sys
sys.path.insert(0, '..')

from app import app
from werkzeug.serving import run_simple

class PrefixFix(object):
	def __init__(self, app, script_name):
		self.app = app
		self.script_name = script_name

	def __call__(self, environ, start_response):
		path_info = environ.get('PATH_INFO', '')
		environ['SCRIPT_NAME'] = self.script_name
		if path_info.startswith(self.script_name):
			environ['PATH_INFO'] = path_info[len(self.script_name):]
		return self.app(environ, start_response)

app.wsgi_app = PrefixFix(app.wsgi_app, '/georefine')
#app.config['SERVER_NAME'] = 'localhost:5000'
app.config['SERVER_NAME'] = None
app.config['APPLICATION_ROOT'] = 'georefine'
app.config['DEBUG'] = True
#app.run(debug=True)
run_simple('localhost', 5000, app.wsgi_app, use_reloader=True, use_debugger=True)
