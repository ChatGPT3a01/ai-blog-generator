import logging
import sys
from pathlib import Path
from flask import Flask, send_from_directory
from flask_cors import CORS
from backend.config import Config
from backend.routes import register_routes


def setup_logging():
    """Setup logging system"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter(
        '\n%(asctime)s | %(levelname)-8s | %(name)s\n'
        '  -> %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    logging.getLogger('backend').setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    return root_logger


def create_app():
    logger = setup_logging()
    logger.info("Starting AI Blog Generator...")

    frontend_dist = Path(__file__).parent.parent / 'frontend' / 'dist'
    if frontend_dist.exists():
        logger.info("[OK] Frontend build detected, enabling static file hosting")
        app = Flask(
            __name__,
            static_folder=str(frontend_dist),
            static_url_path=''
        )
    else:
        logger.info("[DEV] Development mode, start frontend separately")
        app = Flask(__name__)

    app.config.from_object(Config)

    CORS(app, resources={
        r"/api/*": {
            "origins": Config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    })

    register_routes(app)

    _validate_config_on_startup(logger)

    if frontend_dist.exists():
        @app.route('/')
        def serve_index():
            return send_from_directory(app.static_folder, 'index.html')

        @app.errorhandler(404)
        def fallback(e):
            return send_from_directory(app.static_folder, 'index.html')
    else:
        @app.route('/')
        def index():
            return {
                "message": "AI 部落格圖文生成器 API",
                "version": "0.1.0",
                "endpoints": {
                    "health": "/api/health",
                    "outline": "POST /api/outline",
                    "generate": "POST /api/generate",
                    "images": "GET /api/images/<filename>"
                }
            }

    return app


def _validate_config_on_startup(logger):
    """Validate config on startup"""
    from pathlib import Path
    import yaml

    logger.info("Checking config files...")

    text_config_path = Path(__file__).parent.parent / 'text_providers.yaml'
    if text_config_path.exists():
        try:
            with open(text_config_path, 'r', encoding='utf-8') as f:
                text_config = yaml.safe_load(f) or {}
            active = text_config.get('active_provider', 'not set')
            providers = list(text_config.get('providers', {}).keys())
            logger.info(f"[OK] Text config: active={active}, providers={providers}")

            if active in text_config.get('providers', {}):
                provider = text_config['providers'][active]
                if not provider.get('api_key'):
                    logger.warning(f"[WARN] Text provider [{active}] API Key not set")
                else:
                    logger.info(f"[OK] Text provider [{active}] API Key configured")
        except Exception as e:
            logger.error(f"[ERROR] Failed to read text_providers.yaml: {e}")
    else:
        logger.warning("[WARN] text_providers.yaml not found, using defaults")

    image_config_path = Path(__file__).parent.parent / 'image_providers.yaml'
    if image_config_path.exists():
        try:
            with open(image_config_path, 'r', encoding='utf-8') as f:
                image_config = yaml.safe_load(f) or {}
            active = image_config.get('active_provider', 'not set')
            providers = list(image_config.get('providers', {}).keys())
            logger.info(f"[OK] Image config: active={active}, providers={providers}")

            if active in image_config.get('providers', {}):
                provider = image_config['providers'][active]
                if not provider.get('api_key'):
                    logger.warning(f"[WARN] Image provider [{active}] API Key not set")
                else:
                    logger.info(f"[OK] Image provider [{active}] API Key configured")
        except Exception as e:
            logger.error(f"[ERROR] Failed to read image_providers.yaml: {e}")
    else:
        logger.warning("[WARN] image_providers.yaml not found, using defaults")

    logger.info("[OK] Config check completed")


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
