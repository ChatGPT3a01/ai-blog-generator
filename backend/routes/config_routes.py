"""
設定管理相關 API 路由

包含功能：
- 取得目前設定
- 更新設定
- 測試服務商連線
"""

import logging
from pathlib import Path
import yaml
from flask import Blueprint, request, jsonify
from .utils import prepare_providers_for_response

logger = logging.getLogger(__name__)

# 設定檔路徑
CONFIG_DIR = Path(__file__).parent.parent.parent
IMAGE_CONFIG_PATH = CONFIG_DIR / 'image_providers.yaml'
TEXT_CONFIG_PATH = CONFIG_DIR / 'text_providers.yaml'


def create_config_blueprint():
    """建立設定路由藍圖（工廠函數，支援多次呼叫）"""
    config_bp = Blueprint('config', __name__)

    # ==================== 設定讀寫 ====================

    @config_bp.route('/config', methods=['GET'])
    def get_config():
        """
        取得目前設定

        回傳：
        - success: 是否成功
        - config: 設定物件
          - text_generation: 文字生成設定
          - image_generation: 圖片生成設定
        """
        try:
            # 讀取圖片生成設定
            image_config = _read_config(IMAGE_CONFIG_PATH, {
                'active_provider': 'google_genai',
                'providers': {}
            })

            # 讀取文字生成設定
            text_config = _read_config(TEXT_CONFIG_PATH, {
                'active_provider': 'google_gemini',
                'providers': {}
            })

            return jsonify({
                "success": True,
                "config": {
                    "text_generation": {
                        "active_provider": text_config.get('active_provider', ''),
                        "providers": prepare_providers_for_response(
                            text_config.get('providers', {})
                        )
                    },
                    "image_generation": {
                        "active_provider": image_config.get('active_provider', ''),
                        "providers": prepare_providers_for_response(
                            image_config.get('providers', {})
                        )
                    }
                }
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"取得設定失敗: {str(e)}"
            }), 500

    @config_bp.route('/config', methods=['POST'])
    def update_config():
        """
        更新設定

        請求內容：
        - image_generation: 圖片生成設定（可選）
        - text_generation: 文字生成設定（可選）

        回傳：
        - success: 是否成功
        - message: 結果訊息
        """
        try:
            data = request.get_json()

            # 更新圖片生成設定
            if 'image_generation' in data:
                _update_provider_config(
                    IMAGE_CONFIG_PATH,
                    data['image_generation']
                )

            # 更新文字生成設定
            if 'text_generation' in data:
                _update_provider_config(
                    TEXT_CONFIG_PATH,
                    data['text_generation']
                )

            # 清除設定快取，確保下次使用時讀取新設定
            _clear_config_cache()

            return jsonify({
                "success": True,
                "message": "設定已儲存"
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"更新設定失敗: {str(e)}"
            }), 500

    # ==================== 連線測試 ====================

    @config_bp.route('/config/test', methods=['POST'])
    def test_connection():
        """
        測試服務商連線

        請求內容：
        - type: 服務商類型（google_genai/google_gemini/openai_compatible/image_api）
        - provider_name: 服務商名稱（用於從設定讀取 API Key）
        - api_key: API Key（可選，若不提供則從設定讀取）
        - base_url: Base URL（可選）
        - model: 模型名稱（可選）

        回傳：
        - success: 是否成功
        - message: 測試結果訊息
        """
        try:
            data = request.get_json()
            provider_type = data.get('type')
            provider_name = data.get('provider_name')

            if not provider_type:
                return jsonify({"success": False, "error": "缺少 type 參數"}), 400

            # 建立設定
            config = {
                'api_key': data.get('api_key'),
                'base_url': data.get('base_url'),
                'model': data.get('model')
            }

            # 如果沒有提供 api_key，從設定檔讀取
            if not config['api_key'] and provider_name:
                config = _load_provider_config(provider_type, provider_name, config)

            if not config['api_key']:
                return jsonify({"success": False, "error": "API Key 未設定"}), 400

            # 根據類型執行測試
            result = _test_provider_connection(provider_type, config)
            return jsonify(result), 200 if result['success'] else 400

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    return config_bp


# ==================== 輔助函數 ====================

def _read_config(path: Path, default: dict) -> dict:
    """讀取設定檔"""
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or default
    return default


def _write_config(path: Path, config: dict):
    """寫入設定檔"""
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)


def _update_provider_config(config_path: Path, new_data: dict):
    """
    更新服務商設定

    Args:
        config_path: 設定檔路徑
        new_data: 新的設定資料
    """
    # 讀取現有設定
    existing_config = _read_config(config_path, {'providers': {}})

    # 更新 active_provider
    if 'active_provider' in new_data:
        existing_config['active_provider'] = new_data['active_provider']

    # 更新 providers
    if 'providers' in new_data:
        existing_providers = existing_config.get('providers', {})
        new_providers = new_data['providers']

        for name, new_provider_config in new_providers.items():
            # 如果新設定的 api_key 是空的，保留原有的
            if new_provider_config.get('api_key') in [True, False, '', None]:
                if name in existing_providers and existing_providers[name].get('api_key'):
                    new_provider_config['api_key'] = existing_providers[name]['api_key']
                else:
                    new_provider_config.pop('api_key', None)

            # 移除不需要儲存的欄位
            new_provider_config.pop('api_key_env', None)
            new_provider_config.pop('api_key_masked', None)

        existing_config['providers'] = new_providers

    # 儲存設定
    _write_config(config_path, existing_config)


def _clear_config_cache():
    """清除設定快取"""
    try:
        from backend.config import Config
        Config._image_providers_config = None
    except Exception:
        pass

    try:
        from backend.services.image import reset_image_service
        reset_image_service()
    except Exception:
        pass


def _load_provider_config(provider_type: str, provider_name: str, config: dict) -> dict:
    """
    從設定檔載入服務商設定

    Args:
        provider_type: 服務商類型
        provider_name: 服務商名稱
        config: 目前設定（會被合併）

    Returns:
        dict: 合併後的設定
    """
    # 確定設定檔路徑
    if provider_type in ['openai_compatible', 'google_gemini']:
        config_path = TEXT_CONFIG_PATH
    else:
        config_path = IMAGE_CONFIG_PATH

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f) or {}
            providers = yaml_config.get('providers', {})

            if provider_name in providers:
                saved = providers[provider_name]
                config['api_key'] = saved.get('api_key')

                if not config['base_url']:
                    config['base_url'] = saved.get('base_url')
                if not config['model']:
                    config['model'] = saved.get('model')

    return config


def _test_provider_connection(provider_type: str, config: dict) -> dict:
    """
    測試服務商連線

    Args:
        provider_type: 服務商類型
        config: 服務商設定

    Returns:
        dict: 測試結果
    """
    test_prompt = "請回覆'你好'"

    if provider_type == 'google_genai':
        return _test_google_genai(config)

    elif provider_type == 'google_gemini':
        return _test_google_gemini(config, test_prompt)

    elif provider_type == 'openai_compatible':
        return _test_openai_compatible(config, test_prompt)

    elif provider_type == 'image_api':
        return _test_image_api(config)

    else:
        raise ValueError(f"不支援的類型: {provider_type}")


def _test_google_genai(config: dict) -> dict:
    """測試 Google GenAI 圖片生成服務"""
    from google import genai

    if config.get('base_url'):
        client = genai.Client(
            api_key=config['api_key'],
            http_options={
                'base_url': config['base_url'],
                'api_version': 'v1beta'
            },
            vertexai=False
        )
        # 測試列出模型
        try:
            list(client.models.list())
            return {
                "success": True,
                "message": "連線成功！僅代表連線穩定，不確定是否可以穩定支援圖片生成"
            }
        except Exception as e:
            raise Exception(f"連線測試失敗: {str(e)}")
    else:
        return {
            "success": True,
            "message": "Vertex AI 無法透過 API Key 測試連線（需要 OAuth2 認證）。請在實際生成圖片時驗證設定是否正確。"
        }


def _test_google_gemini(config: dict, test_prompt: str) -> dict:
    """測試 Google Gemini 文字生成服務"""
    from google import genai

    if config.get('base_url'):
        client = genai.Client(
            api_key=config['api_key'],
            http_options={
                'base_url': config['base_url'],
                'api_version': 'v1beta'
            },
            vertexai=False
        )
    else:
        client = genai.Client(
            api_key=config['api_key'],
            vertexai=True
        )

    model = config.get('model') or 'gemini-2.0-flash-exp'
    response = client.models.generate_content(
        model=model,
        contents=test_prompt
    )
    result_text = response.text if hasattr(response, 'text') else str(response)

    return _check_response(result_text)


def _test_openai_compatible(config: dict, test_prompt: str) -> dict:
    """測試 OpenAI 相容介面"""
    import requests

    base_url = config['base_url'].rstrip('/').rstrip('/v1') if config.get('base_url') else 'https://api.openai.com'
    url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": config.get('model') or 'gpt-3.5-turbo',
        "messages": [{"role": "user", "content": test_prompt}],
        "max_tokens": 50
    }

    response = requests.post(
        url,
        headers={
            'Authorization': f"Bearer {config['api_key']}",
            'Content-Type': 'application/json'
        },
        json=payload,
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

    result = response.json()
    result_text = result['choices'][0]['message']['content']

    return _check_response(result_text)


def _test_image_api(config: dict) -> dict:
    """測試圖片 API 連線"""
    import requests

    base_url = config['base_url'].rstrip('/').rstrip('/v1') if config.get('base_url') else 'https://api.openai.com'
    url = f"{base_url}/v1/models"

    response = requests.get(
        url,
        headers={'Authorization': f"Bearer {config['api_key']}"},
        timeout=30
    )

    if response.status_code == 200:
        return {
            "success": True,
            "message": "連線成功！僅代表連線穩定，不確定是否可以穩定支援圖片生成"
        }
    else:
        raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")


def _check_response(result_text: str) -> dict:
    """檢查回應是否符合預期"""
    if "你好" in result_text:
        return {
            "success": True,
            "message": f"連線成功！回應: {result_text[:100]}"
        }
    else:
        return {
            "success": True,
            "message": f"連線成功，但回應內容不符合預期: {result_text[:100]}"
        }
