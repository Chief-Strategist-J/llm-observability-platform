from flask import Flask
from services.shared.logging import bootstrap_langsmith
from services.api.routes.chat import chat_bp
from services.api.routes.health import health_bp
from services.api.routes.model import model_bp
from services.api.routes.manage import manage_bp
from services.api.routes.agents import agents_bp
from services.api.routes.rag import rag_bp

bootstrap_langsmith()

app = Flask(__name__)

app.register_blueprint(chat_bp)
app.register_blueprint(health_bp)
app.register_blueprint(model_bp)
app.register_blueprint(manage_bp)
app.register_blueprint(agents_bp)
app.register_blueprint(rag_bp)
