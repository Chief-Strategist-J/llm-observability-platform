from flask import Flask, request, jsonify
import subprocess
import os
from routes.chat import chat_bp
from routes.health import health_bp
from routes.model import model_bp
from routes.manage import manage_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(health_bp)
app.register_blueprint(model_bp)
app.register_blueprint(manage_bp)
