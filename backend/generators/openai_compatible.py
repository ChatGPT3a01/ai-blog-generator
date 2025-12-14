"""OpenAI Compatible Image Generator"""
import logging
import time
import random
import base64
from functools import wraps
from typing import Dict, Any
import requests
from .base import ImageGeneratorBase

logger = logging.getLogger(__name__)


def retry_on_error(max_retries=5, base_delay=3):
    """Auto retry decorator for errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e)
                    # Check if rate limit error
                    if "429" in error_str or "rate" in error_str.lower():
                        if attempt < max_retries - 1:
                            wait_time = (base_delay ** attempt) + random.uniform(0, 1)
                            logger.warning(f"Rate limit hit, retrying in {wait_time:.1f}s (attempt {attempt + 2}/{max_retries})")
                            time.sleep(wait_time)
                            continue
                    # Other errors or retries exhausted
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"Request failed: {error_str[:100]}, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    raise
            logger.error(f"Image generation failed after {max_retries} retries")
            raise Exception(
                f"Image generation failed after {max_retries} retries.\n"
                "Possible causes:\n"
                "1. API rate limit or quota exceeded\n"
                "2. Network connection unstable\n"
                "3. API service temporarily unavailable\n"
                "Suggestion: Try again later, or check API quota and network status"
            )
        return wrapper
    return decorator


class OpenAICompatibleGenerator(ImageGeneratorBase):
    """OpenAI Compatible Image Generator"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        logger.debug("Initializing OpenAICompatibleGenerator...")

        if not self.api_key:
            logger.error("OpenAI Compatible API Key not configured")
            raise ValueError(
                "OpenAI Compatible API Key not configured.\n"
                "Solution: Edit this provider in system settings and fill in the API Key"
            )

        if not self.base_url:
            logger.error("OpenAI Compatible API Base URL not configured")
            raise ValueError(
                "OpenAI Compatible API Base URL not configured.\n"
                "Solution: Edit this provider in system settings and fill in the Base URL"
            )

        # Normalize base_url: remove trailing /v1
        self.base_url = self.base_url.rstrip('/').rstrip('/v1')

        # Default model
        self.default_model = config.get('model', 'dall-e-3')

        # API endpoint type: supports full path (e.g. '/v1/images/generations') or shorthand ('images', 'chat')
        endpoint_type = config.get('endpoint_type', '/v1/images/generations')
        # Compatible with old shorthand format
        if endpoint_type == 'images':
            endpoint_type = '/v1/images/generations'
        elif endpoint_type == 'chat':
            endpoint_type = '/v1/chat/completions'
        self.endpoint_type = endpoint_type

        logger.info(f"OpenAICompatibleGenerator initialized: base_url={self.base_url}, model={self.default_model}, endpoint={self.endpoint_type}")

    def validate_config(self) -> bool:
        """Validate config"""
        return bool(self.api_key and self.base_url)

    @retry_on_error(max_retries=5, base_delay=3)
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        model: str = None,
        quality: str = "standard",
        **kwargs
    ) -> bytes:
        """
        Generate image

        Args:
            prompt: Prompt text
            size: Image size (e.g. "1024x1024", "2048x2048", "4096x4096")
            model: Model name
            quality: Quality ("standard" or "hd")
            **kwargs: Other parameters

        Returns:
            Image binary data
        """
        if model is None:
            model = self.default_model

        logger.info(f"OpenAI Compatible API generating image: model={model}, size={size}, endpoint={self.endpoint_type}")

        # Decide which API method based on endpoint path
        if 'chat' in self.endpoint_type or 'completions' in self.endpoint_type:
            return self._generate_via_chat_api(prompt, size, model)
        else:
            # Default to images API
            return self._generate_via_images_api(prompt, size, model, quality)

    def _generate_via_images_api(
        self,
        prompt: str,
        size: str,
        model: str,
        quality: str
    ) -> bytes:
        """Generate via images API endpoint"""
        # Ensure endpoint starts with /
        endpoint = self.endpoint_type if self.endpoint_type.startswith('/') else '/' + self.endpoint_type
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"  Sending request to: {url}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json"  # Use base64 format for reliability
        }

        # If model supports quality parameter
        if quality and model.startswith('dall-e'):
            payload["quality"] = quality

        response = requests.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code != 200:
            error_detail = response.text[:500]
            logger.error(f"OpenAI Images API request failed: status={response.status_code}, error={error_detail}")
            raise Exception(
                f"OpenAI Images API request failed (status: {response.status_code})\n"
                f"Error details: {error_detail}\n"
                f"Request URL: {url}\n"
                f"Model: {model}\n"
                "Possible causes:\n"
                "1. Invalid or expired API key\n"
                "2. Incorrect model name or no access\n"
                "3. Invalid request parameters\n"
                "4. API quota exhausted\n"
                "5. Incorrect Base URL configuration\n"
                "Suggestion: Check API key, base_url and model name configuration"
            )

        result = response.json()
        logger.debug(f"  API response: data length={len(result.get('data', []))}")

        if "data" not in result or len(result["data"]) == 0:
            logger.error(f"API returned no image data: {str(result)[:200]}")
            raise ValueError(
                "OpenAI API returned no image data.\n"
                f"Response: {str(result)[:500]}\n"
                "Possible causes:\n"
                "1. Prompt blocked by safety filter\n"
                "2. Model does not support image generation\n"
                "3. Invalid request format\n"
                "Suggestion: Modify prompt or check model configuration"
            )

        image_data = result["data"][0]

        # Handle base64 format
        if "b64_json" in image_data:
            img_bytes = base64.b64decode(image_data["b64_json"])
            logger.info(f"[OK] OpenAI Images API image generated: {len(img_bytes)} bytes")
            return img_bytes

        # Handle URL format
        elif "url" in image_data:
            logger.debug(f"  Downloading image from URL...")
            img_response = requests.get(image_data["url"], timeout=60)
            if img_response.status_code == 200:
                logger.info(f"[OK] OpenAI Images API image generated: {len(img_response.content)} bytes")
                return img_response.content
            else:
                logger.error(f"Download image failed: {img_response.status_code}")
                raise Exception(f"Download image failed: {img_response.status_code}")

        else:
            logger.error(f"Cannot extract image data from response: {str(image_data)[:200]}")
            raise ValueError(
                "Cannot extract image data from API response.\n"
                f"Response data: {str(image_data)[:500]}\n"
                "Possible causes:\n"
                "1. Response format does not contain b64_json or url field\n"
                "2. response_format parameter not effective\n"
                "Suggestion: Check API documentation for image return format"
            )

    def _generate_via_chat_api(
        self,
        prompt: str,
        size: str,
        model: str
    ) -> bytes:
        """
        Generate image via chat/completions endpoint

        Supports multiple return formats:
        1. Markdown image link: ![xxx](url) - used by some providers
        2. Base64 data URL: data:image/xxx;base64,xxx
        3. Plain image URL
        """
        # Ensure endpoint starts with /
        endpoint = self.endpoint_type if self.endpoint_type.startswith('/') else '/' + self.endpoint_type
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Chat API generating image: {url}, model={model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4096,
            "temperature": 1.0
        }

        response = requests.post(url, headers=headers, json=payload, timeout=180)

        if response.status_code != 200:
            error_detail = response.text[:500]
            status_code = response.status_code

            # Detailed error messages
            if status_code == 401:
                raise Exception(
                    "[FAIL] API Key authentication failed\n\n"
                    "[Possible causes]\n"
                    "1. Invalid or expired API Key\n"
                    "2. API Key format error\n\n"
                    "[Solution]\n"
                    "Check API Key in system settings"
                )
            elif status_code == 429:
                raise Exception(
                    "[WAIT] API quota or rate limit\n\n"
                    "[Solution]\n"
                    "1. Try again later\n"
                    "2. Check API quota usage"
                )
            else:
                raise Exception(
                    f"[FAIL] Chat API request failed (status: {status_code})\n\n"
                    f"[Error details]\n{error_detail[:300]}\n\n"
                    f"[Request URL] {url}\n"
                    f"[Model] {model}"
                )

        result = response.json()
        logger.debug(f"Chat API response: {str(result)[:500]}")

        # Parse response
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]

                if isinstance(content, str):
                    # 1. Try to parse Markdown image link: ![xxx](url)
                    image_urls = self._extract_markdown_image_urls(content)
                    if image_urls:
                        # Download first image
                        logger.info(f"Extracted {len(image_urls)} images from Markdown, downloading first one...")
                        return self._download_image(image_urls[0])

                    # 2. Try to parse Base64 data URL
                    if content.startswith("data:image"):
                        logger.info("Detected Base64 image data")
                        base64_data = content.split(",")[1]
                        return base64.b64decode(base64_data)

                    # 3. Try as plain URL
                    if content.startswith("http://") or content.startswith("https://"):
                        logger.info("Detected image URL")
                        return self._download_image(content.strip())

        raise ValueError(
            "[FAIL] Cannot extract image data from Chat API response\n\n"
            f"[Response]\n{str(result)[:500]}\n\n"
            "[Possible causes]\n"
            "1. This model does not support image generation\n"
            "2. Response format does not match expected\n"
            "3. Prompt blocked by safety filter\n\n"
            "[Solution]\n"
            "1. Confirm model name is correct\n"
            "2. Modify prompt and retry"
        )

    def _extract_markdown_image_urls(self, content: str) -> list:
        """
        Extract image URLs from Markdown content

        Supports format: ![alt text](url) or ![](url)
        """
        import re
        # Match ![any text](url) format
        pattern = r'!\[.*?\]\((https?://[^\s\)]+)\)'
        urls = re.findall(pattern, content)
        logger.debug(f"Extracted {len(urls)} image URLs from Markdown")
        return urls

    def _download_image(self, url: str) -> bytes:
        """Download image and return binary data"""
        logger.info(f"Downloading image: {url[:100]}...")
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                logger.info(f"[OK] Image downloaded: {len(response.content)} bytes")
                return response.content
            else:
                raise Exception(f"Download image failed: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            raise Exception("[FAIL] Download image timeout, please retry")
        except Exception as e:
            raise Exception(f"[FAIL] Download image failed: {str(e)}")

    def get_supported_sizes(self) -> list:
        """Get supported image sizes"""
        # Default OpenAI supported sizes
        return self.config.get('supported_sizes', [
            "1024x1024",
            "1792x1024",
            "1024x1792",
            "2048x2048",
            "4096x4096"
        ])
