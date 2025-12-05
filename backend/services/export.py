"""匯出服務 - 支援 Markdown 和 HTML 格式"""
import logging
import os
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ExportService:
    """匯出服務類"""

    def __init__(self):
        self.history_root_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )

    def _parse_page_content(self, content: str) -> Dict[str, str]:
        """
        解析頁面內容，提取標題和正文

        Args:
            content: 頁面原始內容

        Returns:
            包含 title 和 body 的字典
        """
        lines = content.strip().split('\n')
        title = ""
        body_lines = []
        in_body = False

        for line in lines:
            line = line.strip()
            # 跳過類型標記
            if re.match(r'\[.*\]', line):
                continue
            # 處理標題行
            if line.startswith('標題：') or line.startswith('标题：'):
                title = line.replace('標題：', '').replace('标题：', '').strip()
            elif line.startswith('副標題：') or line.startswith('副标题：'):
                # 副標題作為正文的一部分
                subtitle = line.replace('副標題：', '').replace('副标题：', '').strip()
                if subtitle:
                    body_lines.append(f"*{subtitle}*")
            elif line.startswith('配圖建議：') or line.startswith('配图建议：'):
                # 跳過配圖建議
                continue
            elif line:
                body_lines.append(line)

        return {
            "title": title,
            "body": '\n'.join(body_lines)
        }

    def export_to_markdown(
        self,
        task_id: str,
        pages: List[Dict[str, Any]],
        include_images: bool = True,
        image_base_url: str = "/api/images"
    ) -> str:
        """
        匯出為 Markdown 格式

        Args:
            task_id: 任務 ID
            pages: 頁面列表
            include_images: 是否包含圖片
            image_base_url: 圖片 URL 前綴

        Returns:
            Markdown 格式的文章內容
        """
        markdown_parts = []

        for page in pages:
            page_type = page.get("type", "content")
            content = page.get("content", "")
            index = page.get("index", 0)

            parsed = self._parse_page_content(content)

            if page_type == "cover":
                # 封面：大標題
                if parsed["title"]:
                    markdown_parts.append(f"# {parsed['title']}\n")
                if parsed["body"]:
                    markdown_parts.append(f"{parsed['body']}\n")
            elif page_type == "intro":
                # 前言
                markdown_parts.append("## 前言\n")
                if parsed["body"]:
                    markdown_parts.append(f"{parsed['body']}\n")
            elif page_type == "summary":
                # 結論
                markdown_parts.append("## 結論\n")
                if parsed["body"]:
                    markdown_parts.append(f"{parsed['body']}\n")
            else:
                # 一般內容
                # 嘗試從內容中提取小標題
                lines = parsed["body"].split('\n')
                if lines and not lines[0].startswith('•') and not lines[0].startswith('-'):
                    first_line = lines[0].strip()
                    if len(first_line) < 50 and not first_line.endswith('：'):
                        markdown_parts.append(f"## {first_line}\n")
                        markdown_parts.append('\n'.join(lines[1:]) + '\n')
                    else:
                        markdown_parts.append(f"{parsed['body']}\n")
                else:
                    markdown_parts.append(f"{parsed['body']}\n")

            # 添加圖片
            if include_images:
                image_url = f"{image_base_url}/{task_id}/{index}.png"
                markdown_parts.append(f"\n![圖片 {index + 1}]({image_url})\n")

            markdown_parts.append("\n---\n\n")

        # 移除最後的分隔線
        result = ''.join(markdown_parts)
        if result.endswith("\n---\n\n"):
            result = result[:-6]

        return result

    def export_to_html(
        self,
        task_id: str,
        pages: List[Dict[str, Any]],
        include_images: bool = True,
        image_base_url: str = "/api/images",
        include_style: bool = True
    ) -> str:
        """
        匯出為 HTML 格式

        Args:
            task_id: 任務 ID
            pages: 頁面列表
            include_images: 是否包含圖片
            image_base_url: 圖片 URL 前綴
            include_style: 是否包含內建樣式

        Returns:
            HTML 格式的文章內容
        """
        html_parts = []

        # 添加樣式
        if include_style:
            html_parts.append("""<style>
.blog-article {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.8;
    color: #333;
}
.blog-article h1 {
    font-size: 2em;
    margin-bottom: 0.5em;
    color: #1a1a1a;
}
.blog-article h2 {
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    color: #2a2a2a;
    border-bottom: 2px solid #eee;
    padding-bottom: 0.3em;
}
.blog-article p {
    margin-bottom: 1em;
}
.blog-article img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 1em 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.blog-article ul, .blog-article ol {
    padding-left: 1.5em;
    margin-bottom: 1em;
}
.blog-article li {
    margin-bottom: 0.5em;
}
.blog-article .subtitle {
    font-style: italic;
    color: #666;
    margin-bottom: 1.5em;
}
.blog-article hr {
    border: none;
    border-top: 1px solid #eee;
    margin: 2em 0;
}
</style>
""")

        html_parts.append('<article class="blog-article">\n')

        for page in pages:
            page_type = page.get("type", "content")
            content = page.get("content", "")
            index = page.get("index", 0)

            parsed = self._parse_page_content(content)

            if page_type == "cover":
                if parsed["title"]:
                    html_parts.append(f'<h1>{self._escape_html(parsed["title"])}</h1>\n')
                if parsed["body"]:
                    html_parts.append(f'<p class="subtitle">{self._format_html_content(parsed["body"])}</p>\n')
            elif page_type == "intro":
                html_parts.append('<h2>前言</h2>\n')
                if parsed["body"]:
                    html_parts.append(f'<div>{self._format_html_content(parsed["body"])}</div>\n')
            elif page_type == "summary":
                html_parts.append('<h2>結論</h2>\n')
                if parsed["body"]:
                    html_parts.append(f'<div>{self._format_html_content(parsed["body"])}</div>\n')
            else:
                lines = parsed["body"].split('\n')
                if lines and not lines[0].startswith('•') and not lines[0].startswith('-'):
                    first_line = lines[0].strip()
                    if len(first_line) < 50 and not first_line.endswith('：'):
                        html_parts.append(f'<h2>{self._escape_html(first_line)}</h2>\n')
                        html_parts.append(f'<div>{self._format_html_content(chr(10).join(lines[1:]))}</div>\n')
                    else:
                        html_parts.append(f'<div>{self._format_html_content(parsed["body"])}</div>\n')
                else:
                    html_parts.append(f'<div>{self._format_html_content(parsed["body"])}</div>\n')

            # 添加圖片
            if include_images:
                image_url = f"{image_base_url}/{task_id}/{index}.png"
                html_parts.append(f'<img src="{image_url}" alt="圖片 {index + 1}" loading="lazy">\n')

            html_parts.append('<hr>\n')

        html_parts.append('</article>\n')

        # 移除最後的 hr
        result = ''.join(html_parts)
        result = result.replace('<hr>\n</article>', '</article>')

        return result

    def _escape_html(self, text: str) -> str:
        """轉義 HTML 特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def _format_html_content(self, text: str) -> str:
        """格式化內容為 HTML"""
        lines = text.split('\n')
        result = []
        in_list = False

        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                continue

            # 處理列表項
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = line.lstrip('•-* ').strip()
                result.append(f'<li>{self._escape_html(item)}</li>')
            # 處理編號列表
            elif re.match(r'^\d+\.', line):
                if not in_list:
                    result.append('<ol>')
                    in_list = True
                item = re.sub(r'^\d+\.\s*', '', line).strip()
                result.append(f'<li>{self._escape_html(item)}</li>')
            else:
                if in_list:
                    result.append('</ul>' if '•' in text or '-' in text else '</ol>')
                    in_list = False
                result.append(f'<p>{self._escape_html(line)}</p>')

        if in_list:
            result.append('</ul>')

        return '\n'.join(result)


def get_export_service() -> ExportService:
    """獲取匯出服務實例"""
    return ExportService()
