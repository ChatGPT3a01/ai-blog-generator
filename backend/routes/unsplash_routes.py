"""
Unsplash 圖庫搜尋 API 路由

當 AI 圖片生成失敗時，提供 Unsplash 免費圖庫作為備用選項
"""

import logging
import requests
from pathlib import Path
from flask import Blueprint, request, jsonify
import yaml

logger = logging.getLogger(__name__)

# 設定檔路徑
CONFIG_PATH = Path(__file__).parent.parent.parent / 'upload_config.yaml'


def _load_config() -> dict:
    """載入設定"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"載入設定失敗: {e}")
        return {}


def _save_config(config: dict) -> bool:
    """儲存設定"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"儲存設定失敗: {e}")
        return False


def create_unsplash_blueprint():
    """建立 Unsplash 路由藍圖"""
    unsplash_bp = Blueprint('unsplash', __name__)

    @unsplash_bp.route('/config', methods=['GET'])
    def get_unsplash_config():
        """
        取得 Unsplash 設定狀態

        回傳：
        - success: 是否成功
        - has_api_key: 是否有設定 API Key
        """
        config = _load_config()
        api_key = config.get('unsplash', {}).get('api_key', '')

        return jsonify({
            'success': True,
            'has_api_key': bool(api_key and len(api_key) > 10)
        })

    @unsplash_bp.route('/config', methods=['POST'])
    def update_unsplash_config():
        """
        更新 Unsplash API Key

        請求體：
        - api_key: Unsplash API Key (Access Key)

        回傳：
        - success: 是否成功
        """
        data = request.get_json()
        api_key = data.get('api_key', '')

        config = _load_config()
        if 'unsplash' not in config:
            config['unsplash'] = {}
        config['unsplash']['api_key'] = api_key

        if _save_config(config):
            return jsonify({
                'success': True,
                'message': 'Unsplash API Key 已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '儲存設定失敗'
            }), 500

    @unsplash_bp.route('/search', methods=['POST'])
    def search_photos():
        """
        搜尋 Unsplash 圖片

        請求體：
        - query: 搜尋關鍵字（必填）
        - per_page: 每頁數量（預設 8）
        - orientation: 方向 (landscape/portrait/squarish，預設 landscape)

        回傳：
        - success: 是否成功
        - photos: 圖片列表
        """
        config = _load_config()
        api_key = config.get('unsplash', {}).get('api_key', '')

        if not api_key or len(api_key) < 10:
            return jsonify({
                'success': False,
                'error': '未設定 Unsplash API Key，請在設定頁面配置'
            }), 400

        data = request.get_json()
        query = data.get('query', '')
        per_page = data.get('per_page', 8)
        orientation = data.get('orientation', 'landscape')

        if not query:
            return jsonify({
                'success': False,
                'error': '請提供搜尋關鍵字'
            }), 400

        try:
            response = requests.get(
                'https://api.unsplash.com/search/photos',
                params={
                    'query': query,
                    'per_page': per_page,
                    'orientation': orientation
                },
                headers={
                    'Authorization': f'Client-ID {api_key}'
                },
                timeout=15
            )

            if response.status_code == 401:
                return jsonify({
                    'success': False,
                    'error': 'Unsplash API Key 無效'
                }), 401

            if response.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'Unsplash API 錯誤: {response.status_code}'
                }), response.status_code

            result = response.json()
            photos = []

            for photo in result.get('results', []):
                photos.append({
                    'id': photo['id'],
                    'thumb': photo['urls']['thumb'],
                    'small': photo['urls']['small'],
                    'regular': photo['urls']['regular'],
                    'full': photo['urls']['full'],
                    'alt': photo.get('alt_description', ''),
                    'photographer': photo['user']['name'],
                    'photographer_url': photo['user']['links']['html']
                })

            return jsonify({
                'success': True,
                'photos': photos,
                'total': result.get('total', 0)
            })

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '搜尋超時，請重試'
            }), 504
        except Exception as e:
            logger.error(f"Unsplash 搜尋錯誤: {e}")
            return jsonify({
                'success': False,
                'error': f'搜尋失敗: {str(e)}'
            }), 500

    @unsplash_bp.route('/download', methods=['POST'])
    def download_photo():
        """
        下載 Unsplash 圖片並儲存到任務目錄

        請求體：
        - photo_url: 圖片 URL (regular 或 full)
        - task_id: 任務 ID
        - index: 圖片索引
        - photo_id: Unsplash 圖片 ID（用於觸發下載計數）

        回傳：
        - success: 是否成功
        - image_url: 本地圖片 URL
        """
        config = _load_config()
        api_key = config.get('unsplash', {}).get('api_key', '')

        data = request.get_json()
        photo_url = data.get('photo_url')
        task_id = data.get('task_id')
        index = data.get('index')
        photo_id = data.get('photo_id')

        if not all([photo_url, task_id, index is not None]):
            return jsonify({
                'success': False,
                'error': '缺少必要參數'
            }), 400

        try:
            # 觸發 Unsplash 下載計數（遵守 API 規範）
            if photo_id and api_key:
                try:
                    requests.get(
                        f'https://api.unsplash.com/photos/{photo_id}/download',
                        headers={'Authorization': f'Client-ID {api_key}'},
                        timeout=5
                    )
                except:
                    pass  # 失敗不影響主流程

            # 下載圖片
            response = requests.get(photo_url, timeout=30)
            if response.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'下載圖片失敗: HTTP {response.status_code}'
                }), 500

            # 儲存到任務目錄
            history_root = Path(__file__).parent.parent.parent / 'history'
            task_dir = history_root / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            filename = f'{index}.png'
            filepath = task_dir / filename

            # 儲存原圖
            with open(filepath, 'wb') as f:
                f.write(response.content)

            # 產生縮圖
            try:
                from backend.utils.image_compressor import compress_image
                thumbnail_data = compress_image(response.content, max_size_kb=50)
                thumbnail_path = task_dir / f'thumb_{filename}'
                with open(thumbnail_path, 'wb') as f:
                    f.write(thumbnail_data)
            except Exception as e:
                logger.warning(f"產生縮圖失敗: {e}")

            return jsonify({
                'success': True,
                'image_url': f'/api/images/{task_id}/{filename}'
            })

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '下載超時，請重試'
            }), 504
        except Exception as e:
            logger.error(f"下載 Unsplash 圖片錯誤: {e}")
            return jsonify({
                'success': False,
                'error': f'下載失敗: {str(e)}'
            }), 500

    return unsplash_bp
