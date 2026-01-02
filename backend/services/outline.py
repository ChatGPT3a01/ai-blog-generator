import logging
import os
import re
import base64
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class OutlineService:
    def __init__(self):
        logger.debug("初始化 OutlineService...")
        self.text_config = self._load_text_config()
        self.client = self._get_client()
        self.prompt_template = self._load_prompt_template()
        logger.info(f"OutlineService 初始化完成，使用服務商: {self.text_config.get('active_provider')}")

    def _load_text_config(self) -> dict:
        """載入文字生成配置"""
        config_path = Path(__file__).parent.parent.parent / 'text_providers.yaml'
        logger.debug(f"載入文字配置: {config_path}")

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                logger.debug(f"文字配置載入成功: active={config.get('active_provider')}")
                return config
            except yaml.YAMLError as e:
                logger.error(f"文字配置 YAML 解析失敗: {e}")
                raise ValueError(
                    f"文字配置檔案格式錯誤: text_providers.yaml\n"
                    f"YAML 解析錯誤: {e}\n"
                    "解決方案：檢查 YAML 縮排和語法"
                )

        logger.warning("text_providers.yaml 不存在，使用預設配置")
        # 預設配置
        return {
            'active_provider': 'google_gemini',
            'providers': {
                'google_gemini': {
                    'type': 'google_gemini',
                    'model': 'gemini-2.0-flash-exp',
                    'temperature': 1.0,
                    'max_output_tokens': 8000
                }
            }
        }

    def _is_valid_api_key(self, api_key: str) -> bool:
        """檢查 API Key 是否有效（非空且非佔位符）"""
        if not api_key:
            return False
        placeholder_patterns = [
            'xxxx', 'your-api-key', 'your_api_key', 'api_key',
            '在此填入', '請填入', 'fill in', 'enter your'
        ]
        api_key_lower = api_key.lower()
        for pattern in placeholder_patterns:
            if pattern in api_key_lower:
                return False
        return len(api_key) >= 10

    def _get_client(self):
        """根據配置取得客戶端"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})

        if not providers:
            logger.error("未找到任何文字生成服務商配置")
            raise ValueError(
                "未找到任何文字生成服務商配置。\n"
                "解決方案：\n"
                "1. 在系統設定頁面新增文字生成服務商\n"
                "2. 或手動編輯 text_providers.yaml 檔案"
            )

        if active_provider not in providers:
            available = ', '.join(providers.keys())
            logger.error(f"文字服務商 [{active_provider}] 不存在，可用: {available}")
            raise ValueError(
                f"未找到文字生成服務商配置: {active_provider}\n"
                f"可用的服務商: {available}\n"
                "解決方案：在系統設定中選擇一個可用的服務商"
            )

        provider_config = providers.get(active_provider, {})

        api_key = provider_config.get('api_key', '')
        if not self._is_valid_api_key(api_key):
            logger.error(f"文字服務商 [{active_provider}] 未配置有效的 API Key")
            raise ValueError(
                f"文字服務商 {active_provider} 未配置有效的 API Key\n"
                "解決方案：在系統設定頁面編輯該服務商，填寫 API Key"
            )

        logger.info(f"使用文字服務商: {active_provider} (type={provider_config.get('type')})")
        return get_text_chat_client(provider_config)

    def _load_prompt_template(self) -> str:
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "outline_prompt.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_outline(self, outline_text: str) -> List[Dict[str, Any]]:
        # 按 <page> 分割页面（兼容旧的 --- 分隔符）
        if '<page>' in outline_text:
            pages_raw = re.split(r'<page>', outline_text, flags=re.IGNORECASE)
        else:
            # 向后兼容：如果没有 <page> 则使用 ---
            pages_raw = outline_text.split("---")

        pages = []

        for index, page_text in enumerate(pages_raw):
            page_text = page_text.strip()
            if not page_text:
                continue

            page_type = "content"
            type_match = re.match(r"\[(\S+)\]", page_text)
            if type_match:
                type_cn = type_match.group(1)
                type_mapping = {
                    "封面": "cover",
                    "前言": "intro",
                    "內容": "content",
                    "内容": "content",
                    "結論": "summary",
                    "总结": "summary",
                }
                page_type = type_mapping.get(type_cn, "content")

            pages.append({
                "index": index,
                "type": page_type,
                "content": page_text
            })

        return pages

    def _get_text_style_prompt(self, style: str) -> str:
        """根據文字風格返回對應的提示詞"""
        style_prompts = {
            # 基本風格
            'professional': '請用【專業解析風】撰寫，條理清楚、段落分明，避免口語與情緒化用詞，像深度教學文章。',
            'teacher': '請用【教師引導風】撰寫，逐步說明概念，適度提出反思問題，引導讀者理解，像老師在課堂說明。',
            'story': '請用【故事敘述風】撰寫，從真實或擬真情境開始，有轉折，最後帶出核心觀點。',
            'opinion': '請用【觀點評論風】撰寫，清楚表達立場，並提出理由與反思，有思辨性。',
            'tutorial': '請用【實戰教學風】撰寫，清楚列出操作步驟與注意事項，讓讀者可實際照做。',
            'summary': '請用【懶人包整理風】撰寫，條列重點，段落簡短、重點明確，好掃讀、易收藏。',
            'social': '請用【社群延伸風】撰寫，語氣自然，像與讀者對話，但仍保持文章結構，節奏感強。',
            'brand': '請用【品牌觀點風】撰寫，結合經驗與價值主張，語氣穩定而有深度，建立作者形象。',
            # 作家風格
            'xuzhimo': '請模仿【徐志摩】的筆風撰寫，浪漫抒情、文字唯美細膩，善用比喻與意象，情感真摯熱烈，如詩如畫。',
            'zhangailing': '請模仿【張愛玲】的筆風撰寫，文字精煉老練、冷靜犀利，帶著蒼涼與世故，善於刻畫人性幽微。',
            'yuguangzhong': '請模仿【余光中】的筆風撰寫，優美典雅、意境悠遠，融合古典與現代，文字有音樂性與節奏感。',
            'sanmao': '請模仿【三毛】的筆風撰寫，率真自然、充滿生命力，文字溫暖浪漫，帶著流浪者的自由與豁達。',
            'linqingxuan': '請模仿【林清玄】的筆風撰寫，禪意淡然、哲理深邃，文字清新雋永，在平凡中見智慧。',
            'baixianyong': '請模仿【白先勇】的筆風撰寫，細膩深沉、情感含蓄，善於描繪人物內心，文字優雅精緻。',
            'longyingtai': '請模仿【龍應台】的筆風撰寫，犀利深刻、理性與感性兼具，觀察敏銳，文字有力量與溫度。',
            'liuyong': '請模仿【劉墉】的筆風撰寫，溫暖勵志、平易近人，善於用故事說道理，文字親切有啟發性。'
        }
        return style_prompts.get(style, style_prompts['professional'])

    def generate_outline(
        self,
        topic: str,
        images: Optional[List[bytes]] = None,
        text_style: str = 'professional'
    ) -> Dict[str, Any]:
        try:
            logger.info(f"開始生成大綱: topic={topic[:50]}..., images={len(images) if images else 0}, style={text_style}")
            prompt = self.prompt_template.format(topic=topic)

            # 加入文字風格提示
            style_prompt = self._get_text_style_prompt(text_style)
            prompt += f"\n\n文字風格要求：{style_prompt}"

            if images and len(images) > 0:
                prompt += f"\n\n注意：使用者提供了 {len(images)} 張參考圖片，請在生成大綱時考慮這些圖片的內容和風格。這些圖片可能是產品圖、個人照片或場景圖，請根據圖片內容來最佳化大綱，使生成的內容與圖片相關聯。"
                logger.debug(f"新增了 {len(images)} 張參考圖片到提示詞")

            # 從配置中取得模型參數
            active_provider = self.text_config.get('active_provider', 'google_gemini')
            providers = self.text_config.get('providers', {})
            provider_config = providers.get(active_provider, {})

            model = provider_config.get('model', 'gemini-2.0-flash-exp')
            temperature = provider_config.get('temperature', 1.0)
            max_output_tokens = provider_config.get('max_output_tokens', 8000)

            logger.info(f"呼叫文字生成 API: model={model}, temperature={temperature}")
            outline_text = self.client.generate_text(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                images=images
            )

            logger.debug(f"API 回傳文字長度: {len(outline_text)} 字元")
            pages = self._parse_outline(outline_text)
            logger.info(f"大綱解析完成，共 {len(pages)} 頁")

            return {
                "success": True,
                "outline": outline_text,
                "pages": pages,
                "has_images": images is not None and len(images) > 0
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"大綱生成失敗: {error_msg}")

            # 根據錯誤類型提供更詳細的錯誤訊息
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
                detailed_error = (
                    f"API 認證失敗。\n"
                    f"錯誤詳情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API Key 無效或已過期\n"
                    "2. API Key 沒有存取該模型的權限\n"
                    "解決方案：在系統設定頁面檢查並更新 API Key"
                )
            elif "model" in error_msg.lower() or "404" in error_msg:
                detailed_error = (
                    f"模型存取失敗。\n"
                    f"錯誤詳情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 模型名稱不正確\n"
                    "2. 沒有存取該模型的權限\n"
                    "解決方案：在系統設定頁面檢查模型名稱設定"
                )
            elif "timeout" in error_msg.lower() or "連接" in error_msg:
                detailed_error = (
                    f"網路連線失敗。\n"
                    f"錯誤詳情: {error_msg}\n"
                    "可能原因：\n"
                    "1. 網路連線不穩定\n"
                    "2. API 服務暫時無法使用\n"
                    "3. Base URL 設定錯誤\n"
                    "解決方案：檢查網路連線，稍後重試"
                )
            elif "rate" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                detailed_error = (
                    f"API 配額限制。\n"
                    f"錯誤詳情: {error_msg}\n"
                    "可能原因：\n"
                    "1. API 呼叫次數超限\n"
                    "2. 帳戶配額用盡\n"
                    "解決方案：等待配額重置，或升級 API 方案"
                )
            else:
                detailed_error = (
                    f"大綱生成失敗。\n"
                    f"錯誤詳情: {error_msg}\n"
                    "可能原因：\n"
                    "1. Text API 設定錯誤或金鑰無效\n"
                    "2. 網路連線問題\n"
                    "3. 模型無法存取或不存在\n"
                    "建議：檢查設定檔 text_providers.yaml"
                )

            return {
                "success": False,
                "error": detailed_error
            }


def get_outline_service() -> OutlineService:
    """
    取得大綱生成服務實例
    每次呼叫都建立新實例以確保配置是最新的
    """
    return OutlineService()
