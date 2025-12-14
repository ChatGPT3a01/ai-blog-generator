"""
Google Blogger 發布服務
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class BloggerService:
    """Google Blogger API 服務"""

    BLOGGER_API_BASE = "https://www.googleapis.com/blogger/v3"

    def __init__(self, access_token: str):
        """
        初始化 Blogger 服務

        Args:
            access_token: Google OAuth2 access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def get_user_blogs(self) -> Dict[str, Any]:
        """取得使用者的所有部落格"""
        url = f"{self.BLOGGER_API_BASE}/users/self/blogs"

        logger.info(f"正在呼叫 Blogger API: {url}")
        logger.info(f"Token 前 20 字元: {self.access_token[:20]}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            logger.info(f"Blogger API 回應狀態碼: {response.status_code}")
            logger.info(f"Blogger API 回應內容: {response.text[:500]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"網路請求失敗: {e}")
            raise Exception(f"網路請求失敗: {e}")

        if response.status_code == 401:
            raise Exception("Token 已過期或無效，請重新授權")
        elif response.status_code == 403:
            raise Exception("權限不足，請確認已授權 Blogger API scope")
        elif response.status_code != 200:
            raise Exception(f"Blogger API 錯誤 ({response.status_code}): {response.text}")

        return response.json()

    def create_post(
        self,
        blog_id: str,
        title: str,
        content: str,
        labels: Optional[list] = None,
        is_draft: bool = False
    ) -> Dict[str, Any]:
        """
        發布文章到 Blogger

        Args:
            blog_id: 部落格 ID
            title: 文章標題
            content: 文章內容（HTML 格式）
            labels: 標籤列表
            is_draft: 是否為草稿

        Returns:
            發布結果
        """
        url = f"{self.BLOGGER_API_BASE}/blogs/{blog_id}/posts"

        if is_draft:
            url += "?isDraft=true"

        post_data = {
            "kind": "blogger#post",
            "title": title,
            "content": content
        }

        if labels:
            post_data["labels"] = labels

        try:
            response = requests.post(url, headers=self.headers, json=post_data, timeout=60)
            logger.info(f"發布文章 API 回應狀態碼: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"發布文章網路請求失敗: {e}")
            raise Exception(f"網路請求失敗: {e}")

        if response.status_code == 401:
            raise Exception("Token 已過期或無效，請重新授權")
        elif response.status_code == 403:
            raise Exception("權限不足，請確認已授權 Blogger API 寫入權限")
        elif response.status_code not in [200, 201]:
            raise Exception(f"發布文章失敗 ({response.status_code}): {response.text}")

        return response.json()


def generate_blog_html(outline: str, images: list, title: str = "") -> str:
    """
    將大綱和圖片轉換為 HTML 格式

    Args:
        outline: 大綱文字
        images: 圖片 URL 列表
        title: 文章標題

    Returns:
        HTML 格式的文章內容
    """
    html_parts = []

    # 解析大綱，將每個段落配上對應的圖片
    sections = outline.split('<page>')

    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # 移除類型標記 [封面]、[前言] 等，但保留內容
        lines = section.split('\n')
        content_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                continue  # 跳過類型標記
            if line.startswith('配圖建議'):
                continue  # 跳過配圖建議
            if line:
                content_lines.append(line)

        if not content_lines:
            continue

        # 第一行作為小標題
        subtitle = content_lines[0] if content_lines else ""
        body = '\n'.join(content_lines[1:]) if len(content_lines) > 1 else ""

        # 組合 HTML
        section_html = f'<h2>{subtitle}</h2>\n'

        # 加入對應的圖片
        if i < len(images) and images[i]:
            section_html += f'<p><img src="{images[i]}" alt="{subtitle}" style="max-width:100%;"/></p>\n'

        # 加入內容
        if body:
            paragraphs = body.split('\n\n')
            for p in paragraphs:
                p = p.strip()
                if p:
                    # 處理列表
                    if p.startswith('•') or p.startswith('-') or p.startswith('*'):
                        items = p.split('\n')
                        section_html += '<ul>\n'
                        for item in items:
                            item = item.strip().lstrip('•-* ')
                            if item:
                                section_html += f'  <li>{item}</li>\n'
                        section_html += '</ul>\n'
                    else:
                        section_html += f'<p>{p.replace(chr(10), "<br/>")}</p>\n'

        html_parts.append(section_html)

    return '\n'.join(html_parts)
