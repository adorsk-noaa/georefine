import sys
import os
import time
import re

__file__ = '/home/adorsk/projects/gr/georefine/webapp/app.py'
_times = {}
watch_pattern = "georefine"

class RollbackImporter:
    def __init__(self):
        self.previousModules = sys.modules.copy()

    def uninstall(self):
        dcount = 0
        for modname in sorted(sys.modules.keys()):
            if modname not in self.previousModules:
                del(sys.modules[modname])
                dcount += 1

class Handler:
    def __init__(self):
        self.rb_importer = RollbackImporter()

    def initTimes(self):
        global _times
        for module in sys.modules.values():
            if self._isValidModule(module):
                self._updateModuleTime(module)

    def _updateModuleTime(self, module):
        global _times
        path = self._getPath(module)
        mtime = os.stat(path).st_mtime
        _times[path] = mtime


    def _getPath(self, module):
        path = module.__file__
        if os.path.splitext(path)[1] in ['.pyc', '.pyo', '.pyd']:
            path = path[:-1]
        path = path.replace('$py.class', '.py')
        return path

    def _moduleIsModified(self, module):
        global _times
        path = self._getPath(module)
        try:
            if not os.path.isfile(path):
                return True
            mtime = os.stat(path).st_mtime
            if mtime != _times.get(path):
                return True
        except:
            return True

        return False

    def _isValidModule(self, module):
        if module and hasattr(module, '__file__') \
                and module.__file__ \
                and module.__name__ != '__main__':
                    return True
        else:
            return False

    def reload_if_modified(self, force_reload=False):
        do_reload = False
        for modname, module in sys.modules.items():
            if modname and re.match(watch_pattern, modname):
                if not self._isValidModule(module): 
                    continue
                if self._moduleIsModified(module):
                    self._updateModuleTime(module)
                    do_reload = True

        if do_reload or force_reload:
            #print "reloading"
            self.rb_importer.uninstall()
            self.rb_importer = RollbackImporter()
            #print len((sys.modules.keys()))
            import georefine.app

h = None
last_check = time.time()
check_time = 5

def handler(environ, start_response):
    global _times, last_check, __file__, check_time, h

    if not h:
        h = Handler()

    now = time.time()
    if not _times:
        h.reload_if_modified(force_reload=True)
        h.initTimes()
        last_check = now
    else:
        if now > (last_check + check_time):
            last_check = now
            h.reload_if_modified()

    return sys.modules['georefine.app'].app.wsgi_app(environ, start_response)


