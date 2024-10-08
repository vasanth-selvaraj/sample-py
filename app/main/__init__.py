import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.main.config import Config

db = SQLAlchemy()

def create_app(config_name=None):
    os.environ['FLASK_CONFIG'] = config_name
    print(config_name)
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app,supports_credentials=True,resources={r"/*": {"origins": "http://localhost:5173"}})
    db.init_app(app)

    from app.main.controller.auth.authController import auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.main.controller.workFlow.workFlowController import workFlowBluePrint
    app.register_blueprint(workFlowBluePrint, url_prefix='/workflow')
    
    return app
