import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


def _is_valid_api_key(api_key: str) -> bool:
    """
    檢查 API Key 是否有效（非空且非佔位符）
    """
    if not api_key:
        return False
    # 檢查常見的佔位符
    placeholder_patterns = [
        'xxxx', 'your-api-key', 'your_api_key', 'api_key',
        '在此填入', '請填入', 'fill in', 'enter your'
    ]
    api_key_lower = api_key.lower()
    for pattern in placeholder_patterns:
        if pattern in api_key_lower:
            return False
    return len(api_key) >= 10  # 有效的 API Key 通常較長


class Config:
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8099
    CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']
    OUTPUT_DIR = 'output'

    _image_providers_config = None
    _text_providers_config = None

    @classmethod
    def load_image_providers_config(cls):
        if cls._image_providers_config is not None:
            return cls._image_providers_config

        config_path = Path(__file__).parent.parent / 'image_providers.yaml'
        logger.debug(f"載入圖片服務商配置: {config_path}")

        if not config_path.exists():
            logger.warning(f"圖片配置檔案不存在: {config_path}，使用預設配置")
            cls._image_providers_config = {
                'active_provider': 'google_genai',
                'providers': {}
            }
            return cls._image_providers_config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._image_providers_config = yaml.safe_load(f) or {}
            logger.debug(f"圖片配置載入成功: {list(cls._image_providers_config.get('providers', {}).keys())}")
        except yaml.YAMLError as e:
            logger.error(f"圖片配置檔案 YAML 格式錯誤: {e}")
            raise ValueError(
                f"配置檔案格式錯誤: image_providers.yaml\n"
                f"YAML 解析錯誤: {e}\n"
                "解決方案：\n"
                "1. 檢查 YAML 縮排是否正確（使用空格，不要用 Tab）\n"
                "2. 檢查引號是否配對\n"
                "3. 使用線上 YAML 驗證器檢查格式"
            )

        return cls._image_providers_config

    @classmethod
    def load_text_providers_config(cls):
        """載入文字生成服務商配置"""
        if cls._text_providers_config is not None:
            return cls._text_providers_config

        config_path = Path(__file__).parent.parent / 'text_providers.yaml'
        logger.debug(f"載入文字服務商配置: {config_path}")

        if not config_path.exists():
            logger.warning(f"文字配置檔案不存在: {config_path}，使用預設配置")
            cls._text_providers_config = {
                'active_provider': 'google_gemini',
                'providers': {}
            }
            return cls._text_providers_config

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._text_providers_config = yaml.safe_load(f) or {}
            logger.debug(f"文字配置載入成功: {list(cls._text_providers_config.get('providers', {}).keys())}")
        except yaml.YAMLError as e:
            logger.error(f"文字配置檔案 YAML 格式錯誤: {e}")
            raise ValueError(
                f"配置檔案格式錯誤: text_providers.yaml\n"
                f"YAML 解析錯誤: {e}\n"
                "解決方案：\n"
                "1. 檢查 YAML 縮排是否正確（使用空格，不要用 Tab）\n"
                "2. 檢查引號是否配對\n"
                "3. 使用線上 YAML 驗證器檢查格式"
            )

        return cls._text_providers_config

    @classmethod
    def get_active_image_provider(cls):
        config = cls.load_image_providers_config()
        active = config.get('active_provider', 'google_genai')
        logger.debug(f"目前啟用的圖片服務商: {active}")
        return active

    @classmethod
    def get_image_provider_config(cls, provider_name: str = None):
        config = cls.load_image_providers_config()

        if provider_name is None:
            provider_name = cls.get_active_image_provider()

        logger.info(f"取得圖片服務商配置: {provider_name}")

        providers = config.get('providers', {})
        if not providers:
            raise ValueError(
                "未找到任何圖片生成服務商配置。\n"
                "解決方案：\n"
                "1. 在系統設定頁面新增圖片生成服務商\n"
                "2. 或手動編輯 image_providers.yaml 檔案\n"
                "3. 確保檔案中有 providers 欄位"
            )

        if provider_name not in providers:
            available = ', '.join(providers.keys()) if providers else '無'
            logger.error(f"圖片服務商 [{provider_name}] 不存在，可用服務商: {available}")
            raise ValueError(
                f"未找到圖片生成服務商配置: {provider_name}\n"
                f"可用的服務商: {available}\n"
                "解決方案：\n"
                "1. 在系統設定頁面新增該服務商\n"
                "2. 或修改 active_provider 為已存在的服務商\n"
                "3. 檢查 image_providers.yaml 檔案"
            )

        provider_config = providers[provider_name].copy()

        # 驗證必要欄位
        api_key = provider_config.get('api_key', '')
        if not _is_valid_api_key(api_key):
            logger.error(f"圖片服務商 [{provider_name}] 未配置有效的 API Key")
            raise ValueError(
                f"服務商 {provider_name} 未配置有效的 API Key\n"
                "解決方案：\n"
                "1. 在系統設定頁面編輯該服務商，填寫 API Key\n"
                "2. 或手動在 image_providers.yaml 中填入有效的 api_key"
            )

        provider_type = provider_config.get('type', provider_name)
        if provider_type in ['openai', 'openai_compatible', 'image_api']:
            if not provider_config.get('base_url'):
                logger.error(f"服務商 [{provider_name}] 類型為 {provider_type}，但未配置 base_url")
                raise ValueError(
                    f"服務商 {provider_name} 未配置 Base URL\n"
                    f"服務商類型 {provider_type} 需要配置 base_url\n"
                    "解決方案：在系統設定頁面編輯該服務商，填寫 Base URL"
                )

        logger.info(f"圖片服務商配置驗證通過: {provider_name} (type={provider_type})")
        return provider_config

    @classmethod
    def reload_config(cls):
        """重新載入配置（清除快取）"""
        logger.info("重新載入所有配置...")
        cls._image_providers_config = None
        cls._text_providers_config = None
