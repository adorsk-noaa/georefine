import sys
import os
import georefine.app

def _getPath(module):
	path = module.__file__
	if os.path.splitext(path)[1] in ['.pyc', '.pyo', '.pyd']:
		path = path[:-1]
	path = path.replace('$py.class', '.py')
	return path

_times = {}
for name, module in sys.modules.items():
	if not module or not 'georefine' in name: continue
	path = _getPath(module)
	mtime = os.stat(path).st_mtime
	_times[path] = mtime

def is_modified(path):
    try:
		if not os.path.isfile(path):
			return True
		mtime = os.stat(path).st_mtime
		if mtime != _times.get(path):
			return True
    except:
        return True

    return False

def _reload(module):
	try: 
		reload(module)
	except: pass
	path = _getPath(module)
	mtime = os.stat(path).st_mtime
	_times[path] = mtime

def reload_sources():
	reload_app = False
	for name, module in sys.modules.items():
		if not module or not 'georefine' in name: continue
		path = _getPath(module)
		if is_modified(path):
			_reload(module)
			reload_app = True
	if reload_app:
		_reload(sys.modules['georefine.app'])

def handler(environ, start_response):
	reload_sources()
	return sys.modules['georefine.app'].app.wsgi_app(environ, start_response)


