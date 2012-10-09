SQLALCHEMY_DATABASE_URI = ""

SECRET_KEY = "KEYSTUB"

UPLOAD_FOLDER = '/tmp'

ALLOWED_EXTENSIONS = set(['txt'])

PROJECT_STATIC_FILES_URL = lambda p: "url_for_%s" % p.id

PROJECT_STATIC_DIR_NAME = "static_dir_stub"

PROJECT_STATIC_FILES_DIR = "static_files_dir_stub"
