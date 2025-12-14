"""
圖片上傳相關 API 路由

包含功能：
- 上傳圖片到 ImgBB
- 取得 ImgBB 配置狀態
"""

import os
import base64
import logging
import requests
from pathlib import Path
from flask import Blueprint, request, jsonify
import yaml

logger = logging.getLogger(__name__)


def create_upload_blueprint():
    """創建上傳路由藍圖"""
    upload_bp = Blueprint('upload', __name__)

    # 配置檔案路徑
    config_path = Path(__file__).parent.parent.parent / 'upload_config.yaml'

    def _load_config():
        """載入上傳配置"""
        if not config_path.exists():
            return {'imgbb': {'api_key': ''}}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {'imgbb': {'api_key': ''}}
        except Exception as e:
            logger.error(f"載入上傳配置失敗: {e}")
            return {'imgbb': {'api_key': ''}}

    def _save_config(config):
        """儲存上傳配置"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True)
            return True
        except Exception as e:
            logger.error(f"儲存上傳配置失敗: {e}")
            return False

    @upload_bp.route('/config', methods=['GET'])
    def get_upload_config():
        """
        取得上傳配置（隱藏 API Key）

        返回：
        - success: 是否成功
        - has_imgbb_key: 是否有設定 ImgBB API Key
        """
        config = _load_config()
        api_key = config.get('imgbb', {}).get('api_key', '')

        return jsonify({
            'success': True,
            'has_imgbb_key': bool(api_key and len(api_key) > 10)
        })

    @upload_bp.route('/config', methods=['POST'])
    def update_upload_config():
        """
        更新上傳配置

        請求體：
        - imgbb_api_key: ImgBB API Key

        返回：
        - success: 是否成功
        """
        data = request.get_json()
        api_key = data.get('imgbb_api_key', '')

        config = _load_config()
        config['imgbb'] = {'api_key': api_key}

        if _save_config(config):
            return jsonify({
                'success': True,
                'message': 'ImgBB API Key 已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '儲存配置失敗'
            }), 500

    @upload_bp.route('/imgbb', methods=['POST'])
    def upload_to_imgbb():
        """
        上傳圖片到 ImgBB

        請求體：
        - image: base64 編碼的圖片 或 圖片 URL
        - task_id: 任務 ID（用於讀取本地圖片）
        - filename: 檔案名稱（用於讀取本地圖片）

        返回：
        - success: 是否成功
        - url: 圖片公開 URL
        - delete_url: 刪除 URL
        """
        config = _load_config()
        api_key = config.get('imgbb', {}).get('api_key', '')

        if not api_key or len(api_key) < 10:
            return jsonify({
                'success': False,
                'error': '未設定 ImgBB API Key，請在設定頁面配置'
            }), 400

        data = request.get_json()
        image_data = data.get('image')
        task_id = data.get('task_id')
        filename = data.get('filename')

        # 如果提供了 task_id 和 filename，從本地讀取圖片
        if task_id and filename:
            history_root = Path(__file__).parent.parent.parent / 'history'
            image_path = history_root / task_id / filename

            if not image_path.exists():
                return jsonify({
                    'success': False,
                    'error': f'圖片不存在: {task_id}/{filename}'
                }), 404

            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

        if not image_data:
            return jsonify({
                'success': False,
                'error': '未提供圖片資料'
            }), 400

        # 移除可能的 data URL 前綴
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        try:
            # 呼叫 ImgBB API
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                data={
                    'key': api_key,
                    'image': image_data
                },
                timeout=30
            )

            result = response.json()

            if response.ok and result.get('success'):
                img_data = result.get('data', {})
                return jsonify({
                    'success': True,
                    'url': img_data.get('url'),
                    'display_url': img_data.get('display_url'),
                    'delete_url': img_data.get('delete_url'),
                    'thumb_url': img_data.get('thumb', {}).get('url')
                })
            else:
                error_msg = result.get('error', {}).get('message', '上傳失敗')
                logger.error(f"ImgBB 上傳失敗: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'ImgBB 上傳失敗: {error_msg}'
                }), 500

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '上傳超時，請重試'
            }), 504
        except Exception as e:
            logger.error(f"上傳到 ImgBB 時發生錯誤: {e}")
            return jsonify({
                'success': False,
                'error': f'上傳失敗: {str(e)}'
            }), 500

    @upload_bp.route('/batch', methods=['POST'])
    def batch_upload():
        """
        批量上傳圖片到 ImgBB

        請求體：
        - images: 圖片列表，每個包含 task_id, filename, index

        返回：
        - success: 是否成功
        - results: 每張圖片的上傳結果
        """
        config = _load_config()
        api_key = config.get('imgbb', {}).get('api_key', '')

        if not api_key or len(api_key) < 10:
            return jsonify({
                'success': False,
                'error': '未設定 ImgBB API Key，請在設定頁面配置'
            }), 400

        data = request.get_json()
        images = data.get('images', [])

        if not images:
            return jsonify({
                'success': False,
                'error': '未提供圖片列表'
            }), 400

        results = []
        history_root = Path(__file__).parent.parent.parent / 'history'

        for img_info in images:
            task_id = img_info.get('task_id')
            filename = img_info.get('filename')
            index = img_info.get('index')

            # 讀取本地圖片
            image_path = history_root / task_id / filename

            if not image_path.exists():
                results.append({
                    'index': index,
                    'success': False,
                    'error': f'圖片不存在'
                })
                continue

            try:
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')

                # 呼叫 ImgBB API
                response = requests.post(
                    'https://api.imgbb.com/1/upload',
                    data={
                        'key': api_key,
                        'image': image_data
                    },
                    timeout=30
                )

                result = response.json()

                if response.ok and result.get('success'):
                    img_data = result.get('data', {})
                    results.append({
                        'index': index,
                        'success': True,
                        'url': img_data.get('url'),
                        'display_url': img_data.get('display_url')
                    })
                else:
                    error_msg = result.get('error', {}).get('message', '上傳失敗')
                    results.append({
                        'index': index,
                        'success': False,
                        'error': error_msg
                    })

            except Exception as e:
                results.append({
                    'index': index,
                    'success': False,
                    'error': str(e)
                })

        success_count = sum(1 for r in results if r.get('success'))

        return jsonify({
            'success': success_count > 0,
            'total': len(images),
            'uploaded': success_count,
            'failed': len(images) - success_count,
            'results': results
        })

    return upload_bp
