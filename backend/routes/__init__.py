"""
API 路由模組

將 API 路由按功能拆分為多個子模組：
- outline_routes: 大綱生成 API
- image_routes: 圖片生成 API
- history_routes: 歷史記錄 API
- config_routes: 設定管理 API
- blogger_routes: Blogger 發布 API
- upload_routes: 圖片上傳 API

所有路由都註冊到 /api 前綴下
"""

from flask import Blueprint


def create_api_blueprint():
    """建立並配置主 API 藍圖"""
    from .outline_routes import create_outline_blueprint
    from .image_routes import create_image_blueprint
    from .history_routes import create_history_blueprint
    from .config_routes import create_config_blueprint
    from .export_routes import create_export_blueprint
    from .blogger_routes import create_blogger_blueprint
    from .upload_routes import create_upload_blueprint

    api_bp = Blueprint('api', __name__, url_prefix='/api')

    api_bp.register_blueprint(create_outline_blueprint())
    api_bp.register_blueprint(create_image_blueprint())
    api_bp.register_blueprint(create_history_blueprint())
    api_bp.register_blueprint(create_config_blueprint())
    api_bp.register_blueprint(create_export_blueprint())
    api_bp.register_blueprint(create_blogger_blueprint())
    api_bp.register_blueprint(create_upload_blueprint(), url_prefix='/upload')

    return api_bp


def register_routes(app):
    """註冊所有 API 路由到 Flask 應用"""
    api_bp = create_api_blueprint()
    app.register_blueprint(api_bp)


__all__ = ['register_routes', 'create_api_blueprint']
