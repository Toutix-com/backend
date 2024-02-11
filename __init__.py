#import all the database models
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .model import db
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '312559'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/new_trial'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app, db)
app.config['JWT_SECRET_KEY'] = '398210'  # Change this to a random secret key
jwt = JWTManager(app)

login = LoginManager(app)
login.login_view = 'auth.unauthorized'

