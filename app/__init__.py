import os
import logging
from flask import Flask

try:
    # load .env if present (optional)
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def create_app():
    """Flask application factory."""
    app = Flask(__name__, instance_relative_config=False)

    # Load config module if present, otherwise env vars are available via os.environ
    try:
        import config as cfg
        app.config.from_object(cfg)
    except Exception:
        for k, v in os.environ.items():
            app.config[k] = v

    # Configure basic logging level
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))

    # Register blueprint routes
    from .routes import bp as alerts_bp
    app.register_blueprint(alerts_bp)

    return app
