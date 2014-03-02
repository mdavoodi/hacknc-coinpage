CSRF_ENABLED = True
DEBUG = True
PER_PAGE = 30
SECRET_KEY = 'development key'
DEBUG = True
FACEBOOK_APP_ID = '1456143767948268'
FACEBOOK_APP_SECRET = '15f78747c468ddb43d6222018c803945'

import os
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

