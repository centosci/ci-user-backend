import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from utils.init_app import set_request, end_request
from flask_cors import CORS

app = Flask(__name__)

db = SQLAlchemy()
migrate = Migrate()

from views import api
from auth.login import auth

app.register_blueprint(api)
app.register_blueprint(auth)

CORS(app, supports_credentials=True)

app.config.from_object(os.environ['APP_SETTINGS'])

db.init_app(app)
migrate.init_app(app, db)

app.before_request(set_request)
app.teardown_request(end_request)
