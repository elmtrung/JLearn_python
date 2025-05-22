from flask import Flask
from flask_cors import CORS
from app.config import CORS_CONFIG
from app.routes import transcribe, translate, payment, collections, admin

def create_app():
    app = Flask(__name__)
    CORS(app, resources={
        r"/*": CORS_CONFIG
    })

    # Register blueprints
    app.register_blueprint(transcribe.bp)
    app.register_blueprint(translate.bp)
    app.register_blueprint(payment.bp)
    app.register_blueprint(collections.bp)
    app.register_blueprint(admin.bp)

    return app 