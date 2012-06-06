import sys

if sys.modules.has_key('georefine.app'):
	reload(sys.modules['georefine.app'])
else:
	import georefine.app

def handler(environ, start_response):

	return sys.modules['georefine.app'].app.wsgi_app(environ, start_response)

