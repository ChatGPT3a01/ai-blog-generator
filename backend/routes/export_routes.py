"""匯出相關路由"""
import logging
from flask import Blueprint, request, jsonify, Response
from backend.services.export import get_export_service

logger = logging.getLogger(__name__)


def create_export_blueprint():
    """創建匯出路由藍圖"""
    export_bp = Blueprint('export', __name__)

    @export_bp.route('/export/markdown', methods=['POST'])
    def export_markdown():
        """
        匯出為 Markdown 格式

        Request body:
        {
            "task_id": "任務ID",
            "pages": [頁面列表],
            "include_images": true,  # 可選，預設 true
            "image_base_url": "/api/images"  # 可選
        }
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "請求資料為空"}), 400

            task_id = data.get('task_id')
            pages = data.get('pages', [])
            include_images = data.get('include_images', True)
            image_base_url = data.get('image_base_url', '/api/images')

            if not task_id:
                return jsonify({"error": "缺少 task_id"}), 400

            if not pages:
                return jsonify({"error": "缺少 pages"}), 400

            service = get_export_service()
            markdown_content = service.export_to_markdown(
                task_id=task_id,
                pages=pages,
                include_images=include_images,
                image_base_url=image_base_url
            )

            return jsonify({
                "success": True,
                "content": markdown_content,
                "format": "markdown"
            })

        except Exception as e:
            logger.error(f"匯出 Markdown 失敗: {str(e)}")
            return jsonify({"error": f"匯出失敗: {str(e)}"}), 500

    @export_bp.route('/export/html', methods=['POST'])
    def export_html():
        """
        匯出為 HTML 格式

        Request body:
        {
            "task_id": "任務ID",
            "pages": [頁面列表],
            "include_images": true,  # 可選，預設 true
            "image_base_url": "/api/images",  # 可選
            "include_style": true  # 可選，是否包含內建樣式
        }
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "請求資料為空"}), 400

            task_id = data.get('task_id')
            pages = data.get('pages', [])
            include_images = data.get('include_images', True)
            image_base_url = data.get('image_base_url', '/api/images')
            include_style = data.get('include_style', True)

            if not task_id:
                return jsonify({"error": "缺少 task_id"}), 400

            if not pages:
                return jsonify({"error": "缺少 pages"}), 400

            service = get_export_service()
            html_content = service.export_to_html(
                task_id=task_id,
                pages=pages,
                include_images=include_images,
                image_base_url=image_base_url,
                include_style=include_style
            )

            return jsonify({
                "success": True,
                "content": html_content,
                "format": "html"
            })

        except Exception as e:
            logger.error(f"匯出 HTML 失敗: {str(e)}")
            return jsonify({"error": f"匯出失敗: {str(e)}"}), 500

    @export_bp.route('/export/download/markdown', methods=['POST'])
    def download_markdown():
        """
        下載 Markdown 文件
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "請求資料為空"}), 400

            task_id = data.get('task_id')
            pages = data.get('pages', [])
            include_images = data.get('include_images', True)
            image_base_url = data.get('image_base_url', '/api/images')

            if not task_id:
                return jsonify({"error": "缺少 task_id"}), 400

            service = get_export_service()
            markdown_content = service.export_to_markdown(
                task_id=task_id,
                pages=pages,
                include_images=include_images,
                image_base_url=image_base_url
            )

            return Response(
                markdown_content,
                mimetype='text/markdown',
                headers={
                    'Content-Disposition': f'attachment; filename=article_{task_id}.md'
                }
            )

        except Exception as e:
            logger.error(f"下載 Markdown 失敗: {str(e)}")
            return jsonify({"error": f"下載失敗: {str(e)}"}), 500

    @export_bp.route('/export/download/html', methods=['POST'])
    def download_html():
        """
        下載 HTML 文件
        """
        try:
            data = request.get_json()

            if not data:
                return jsonify({"error": "請求資料為空"}), 400

            task_id = data.get('task_id')
            pages = data.get('pages', [])
            include_images = data.get('include_images', True)
            image_base_url = data.get('image_base_url', '/api/images')
            include_style = data.get('include_style', True)

            if not task_id:
                return jsonify({"error": "缺少 task_id"}), 400

            service = get_export_service()
            html_content = service.export_to_html(
                task_id=task_id,
                pages=pages,
                include_images=include_images,
                image_base_url=image_base_url,
                include_style=include_style
            )

            # 包裝成完整的 HTML 文件
            full_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>部落格文章</title>
</head>
<body>
{html_content}
</body>
</html>"""

            return Response(
                full_html,
                mimetype='text/html',
                headers={
                    'Content-Disposition': f'attachment; filename=article_{task_id}.html'
                }
            )

        except Exception as e:
            logger.error(f"下載 HTML 失敗: {str(e)}")
            return jsonify({"error": f"下載失敗: {str(e)}"}), 500

    return export_bp
