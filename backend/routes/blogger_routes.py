"""
Google Blogger 發布相關 API 路由
"""

import logging
import re
import requests
from pathlib import Path
from flask import Blueprint, request, jsonify
from backend.services.blogger import BloggerService, generate_blog_html
from backend.config import Config

logger = logging.getLogger(__name__)

# urusai.cc API 端點
URUSAI_API_URL = "https://api.urusai.cc/v1/upload"


def upload_image_to_urusai(image_path: Path) -> str:
    """
    上傳圖片到 urusai.cc 並返回公開 URL

    Args:
        image_path: 圖片檔案路徑

    Returns:
        urusai.cc 圖片 URL，失敗返回空字串
    """
    try:
        with open(image_path, 'rb') as f:
            # 使用 multipart/form-data 上傳
            files = {
                'file': (image_path.name, f, 'image/png')
            }

            response = requests.post(
                URUSAI_API_URL,
                files=files,
                timeout=60
            )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"urusai.cc 回應: {result}")
            # urusai.cc 返回格式: {"status":"success","data":{"url_direct":"..."}}
            data = result.get('data', {})
            direct_url = data.get('url_direct', '') or data.get('url_preview', '') or result.get('direct', '') or result.get('url', '')
            if direct_url:
                logger.info(f"成功上傳圖片到 urusai.cc: {direct_url}")
                return direct_url
            else:
                logger.error(f"urusai.cc 回應中沒有 URL: {result}")
                return ''
        else:
            logger.error(f"urusai.cc 上傳失敗: {response.status_code} - {response.text}")
            return ''

    except Exception as e:
        logger.error(f"上傳圖片到 urusai.cc 失敗: {e}")
        return ''


def convert_images_to_public_urls(images: list) -> list:
    """
    將本地圖片上傳到 urusai.cc 並返回公開 URL

    Args:
        images: 圖片 URL 列表

    Returns:
        公開 URL 列表
    """
    public_urls = []

    for img_url in images:
        if not img_url:
            public_urls.append('')
            continue

        try:
            # 解析 URL 取得檔案路徑
            # URL 格式: /api/images/task_id/filename?thumbnail=false
            match = re.search(r'/api/images/([^/]+)/([^?]+)', img_url)
            if match:
                task_id = match.group(1)
                filename = match.group(2)

                # 構建實際檔案路徑（圖片存在 history 目錄）
                file_path = Path(__file__).parent.parent.parent / "history" / task_id / filename
                logger.info(f"圖片檔案路徑: {file_path}, 存在: {file_path.exists()}")

                if file_path.exists():
                    # 上傳到 urusai.cc
                    public_url = upload_image_to_urusai(file_path)
                    public_urls.append(public_url)
                else:
                    logger.warning(f"圖片檔案不存在: {file_path}")
                    public_urls.append('')
            else:
                # 如果不是本地 URL，直接使用原 URL
                public_urls.append(img_url)

        except Exception as e:
            logger.error(f"處理圖片失敗: {e}")
            public_urls.append('')

    return public_urls


def create_blogger_blueprint():
    """建立 Blogger 路由藍圖"""
    blogger_bp = Blueprint('blogger', __name__)

    @blogger_bp.route('/blogger/blogs', methods=['POST'])
    def get_blogs():
        """
        取得使用者的部落格清單

        請求內容：
        - access_token: Google OAuth2 access token

        回傳：
        - success: 是否成功
        - blogs: 部落格清單
        """
        try:
            data = request.get_json()
            access_token = data.get('access_token')

            if not access_token:
                return jsonify({
                    "success": False,
                    "error": "缺少 access_token"
                }), 400

            service = BloggerService(access_token)
            result = service.get_user_blogs()

            blogs = []
            for blog in result.get('items', []):
                blogs.append({
                    "id": blog.get('id'),
                    "name": blog.get('name'),
                    "url": blog.get('url')
                })

            return jsonify({
                "success": True,
                "blogs": blogs
            })

        except Exception as e:
            error_msg = str(e)
            logger.error(f"取得部落格清單失敗: {error_msg}")

            # 根據錯誤類型決定 HTTP 狀態碼
            if "過期" in error_msg or "無效" in error_msg:
                status_code = 401
            elif "權限不足" in error_msg:
                status_code = 403
            else:
                status_code = 500

            return jsonify({
                "success": False,
                "error": error_msg
            }), status_code

    @blogger_bp.route('/blogger/publish', methods=['POST'])
    def publish_post():
        """
        發布文章到 Blogger

        請求內容：
        - access_token: Google OAuth2 access token
        - blog_id: 部落格 ID
        - title: 文章標題
        - outline: 大綱內容
        - images: 圖片 URL 列表
        - labels: 標籤列表（可選）
        - is_draft: 是否為草稿（可選，預設 false）

        回傳：
        - success: 是否成功
        - post_url: 文章網址
        """
        try:
            data = request.get_json()

            access_token = data.get('access_token')
            blog_id = data.get('blog_id')
            title = data.get('title', '未命名文章')
            outline = data.get('outline', '')
            images = data.get('images', [])
            labels = data.get('labels', [])
            is_draft = data.get('is_draft', False)

            if not access_token:
                return jsonify({
                    "success": False,
                    "error": "缺少 access_token"
                }), 400

            if not blog_id:
                return jsonify({
                    "success": False,
                    "error": "缺少 blog_id"
                }), 400

            # 將本地圖片上傳到 urusai.cc 圖床
            logger.info(f"正在上傳 {len(images)} 張圖片到 urusai.cc...")
            logger.info(f"原始圖片 URL: {images}")
            public_urls = convert_images_to_public_urls(images)
            logger.info(f"轉換後公開 URL: {public_urls}")

            # 將大綱轉換為 HTML（使用公開 URL）
            html_content = generate_blog_html(outline, public_urls, title)
            logger.info(f"生成的 HTML 內容前 500 字元: {html_content[:500]}")

            # 寫入 debug 檔案到專案根目錄
            debug_path = Path(Config.OUTPUT_DIR).parent / "blogger_debug.txt"
            logger.info(f"Debug 檔案路徑: {debug_path}")
            try:
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(f"=== 發布 Debug 資訊 ===\n")
                    f.write(f"標題: {title}\n\n")
                    f.write(f"原始圖片 URL ({len(images)} 張):\n")
                    for i, url in enumerate(images):
                        f.write(f"  [{i}] {url}\n")
                    f.write(f"\n轉換後公開 URL ({len(public_urls)} 張):\n")
                    for i, url in enumerate(public_urls):
                        f.write(f"  [{i}] {url}\n")
                    f.write(f"\n大綱內容:\n{outline}\n")
                    f.write(f"\n生成的 HTML:\n{html_content}\n")
                logger.info(f"Debug 檔案已寫入")
            except Exception as write_err:
                logger.error(f"寫入 debug 檔案失敗: {write_err}")

            # 發布到 Blogger
            service = BloggerService(access_token)
            result = service.create_post(
                blog_id=blog_id,
                title=title,
                content=html_content,
                labels=labels,
                is_draft=is_draft
            )

            return jsonify({
                "success": True,
                "post_url": result.get('url', ''),
                "post_id": result.get('id', ''),
                "message": "草稿已儲存" if is_draft else "文章已發布"
            })

        except Exception as e:
            error_msg = str(e)
            logger.error(f"發布文章失敗: {error_msg}")

            # 根據錯誤類型決定 HTTP 狀態碼
            if "過期" in error_msg or "無效" in error_msg:
                status_code = 401
            elif "權限不足" in error_msg:
                status_code = 403
            else:
                status_code = 500

            return jsonify({
                "success": False,
                "error": error_msg
            }), status_code

    return blogger_bp
