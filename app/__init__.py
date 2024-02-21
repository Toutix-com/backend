#import all the database models
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.model import db
from flask_login import LoginManager
from app.api import api
from app.config import Config
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# app.config['SECRET_KEY'] = '312559'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/new_trial'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ECHO'] = True
app.config.from_object(Config)
app.debug = True
app.register_blueprint(api, url_prefix='/api')
db.init_app(app)

migrate = Migrate(app, db)
app.config['JWT_SECRET_KEY'] = '398210'  # Change this to a random secret key
jwts = JWTManager(app)

login = LoginManager(app)
login.login_view = 'auth.unauthorized'

@app.route("/api/docs")
def api_index():
    acceptable_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    route_list = {rule.rule: [
        [method for method in rule.methods if method in acceptable_methods],
        app.view_functions[rule.endpoint].__doc__]
        for rule in app.url_map.iter_rules() if rule.endpoint != 'static'}
    return route_list