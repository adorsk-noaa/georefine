from georefine.config import config as gr_config

DEBUG = False

SQLALCHEMY_DATABASE_URI = gr_config['DB_URI']

SECRET_KEY = gr_config.get('SECRET_KEY', 'secretawesome')

UPLOAD_FOLDER = '/tmp'

ALLOWED_EXTENSIONS = set(['txt'])

#SERVER_NAME = "localhost:8080"

APPLICATION_ROOT = "georefine"
