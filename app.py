from flask import Flask, request
from flask_jwt_extended import JWTManager
from src.db import init_db
from src.auth_routes import auth_bp
from src.user_routes import user_bp
from src.admin_routes import admin_bp
from src.config import Config
from src.public_routes import public_bp

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)

    # --- JWT Setup ---
    jwt = JWTManager(app)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False if app.config.get("FLASK_ENV") == "development" else True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax" if app.config.get("FLASK_ENV") == "development" else "None"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/"

    # --- JWT Error Handlers (for debugging 422 etc.) ---
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        print("❌ Unauthorized or missing JWT")
        return {"error": "Missing or invalid JWT"}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print("❌ Invalid JWT token:", error)
        return {"error": "Invalid token"}, 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print("⚠️ Token expired for user:", jwt_payload)
        return {"error": "Token expired"}, 401

    # --- ✅ CORS Setup (Manual Headers to Allow Cookies) ---
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            app.config.get("FRONTEND_BASE")
        ]
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    # --- Initialize DB + Routes ---
    init_db(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(public_bp, url_prefix="/api/public")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
