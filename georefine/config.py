SQLALCHEMY_DATABASE_URI = "db_uri_stub"

SECRET_KEY = "key_stub"

UPLOAD_FOLDER = '/tmp'

ALLOWED_EXTENSIONS = set(['txt'])

PROJECT_STATIC_URL = lambda p: "url_for_%s" % p.id

STATIC_DIR = "static_dir_stub"

PROJECT_STATIC_DIR_NAME = "project_static_dir_name"

APPLICATION_ROOT = "georefine"
