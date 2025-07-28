from gevent import monkey
gevent_patch = monkey.patch_all()
import os
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils.error_handler import handle_error
from controllers.auth_controller import auth_bp
from controllers.car_controller import car_bp
from controllers.user_controller import user_bp
from controllers.search_controller import search_bp
from controllers.subscription_controller import subscription_bp
from controllers.payment_controller import payment_bp
from controllers.admin_controller import admin_bp
from services.message_service import MessageService
from flask_socketio import SocketIO

# Configure logging to be less verbose
logging.basicConfig(
    level=logging.WARNING,  # Change from DEBUG to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app)

    app.config.from_object(Config)

    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    app.config['PROFILE_PICS_FOLDER'] = os.path.join(app.static_folder, 'profile_pics')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)

    jwt = JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(car_bp, url_prefix='/api/cars')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(subscription_bp, url_prefix='/api/subscriptions')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    app.register_error_handler(Exception, handle_error)

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)

    return app

app = create_app()

# Initialize SocketIO with gevent
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    logger=False,
    engineio_logger=False
)
message_service = MessageService(socketio)
message_service.init_socketio(socketio)

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "message": "Souq Sayarat API is running"})

for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    print("Starting server on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)