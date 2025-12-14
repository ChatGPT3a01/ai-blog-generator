"""Image Generation Service"""
import logging
import os
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Generator, List, Optional, Tuple
from backend.config import Config
from backend.generators.factory import ImageGeneratorFactory
from backend.utils.image_compressor import compress_image

logger = logging.getLogger(__name__)


class ImageService:
    """Image Generation Service Class"""

    # Concurrency Config
    MAX_CONCURRENT = 15  # Max concurrent
    AUTO_RETRY_COUNT = 3  # Auto retry count

    def __init__(self, provider_name: str = None):
        """
        Initialize image generation service

        Args:
            provider_name: Provider name, if None use the active provider from config
        """
        logger.debug("Initializing ImageService...")

        # Get provider config
        if provider_name is None:
            provider_name = Config.get_active_image_provider()

        logger.info(f"Using image provider: {provider_name}")
        provider_config = Config.get_image_provider_config(provider_name)

        # Create generator instance
        provider_type = provider_config.get('type', provider_name)
        logger.debug(f"Creating generator: type={provider_type}")
        self.generator = ImageGeneratorFactory.create(provider_type, provider_config)

        # Save config info
        self.provider_name = provider_name
        self.provider_config = provider_config

        # Check if short prompt mode is enabled
        self.use_short_prompt = provider_config.get('short_prompt', False)

        # Load prompt templates
        self.prompt_template = self._load_prompt_template()
        self.prompt_template_short = self._load_prompt_template(short=True)

        # History root directory
        self.history_root_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "history"
        )
        os.makedirs(self.history_root_dir, exist_ok=True)

        # Current task output directory
        self.current_task_dir = None

        # Store task states (for retry)
        self._task_states: Dict[str, Dict] = {}

        logger.info(f"ImageService initialized: provider={provider_name}, type={provider_type}")

    def _load_prompt_template(self, short: bool = False) -> str:
        """Load Prompt template"""
        filename = "image_prompt_short.txt" if short else "image_prompt.txt"
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            filename
        )
        if not os.path.exists(prompt_path):
            # If short template doesn't exist, return empty string
            return ""
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _save_image(self, image_data: bytes, filename: str, task_dir: str = None) -> str:
        """
        Save image to local, also generate thumbnail

        Args:
            image_data: Image binary data
            filename: File name
            task_dir: Task directory (if None use current task dir)

        Returns:
            Saved file path
        """
        if task_dir is None:
            task_dir = self.current_task_dir

        if task_dir is None:
            raise ValueError("Task directory not set")

        # Save original image
        filepath = os.path.join(task_dir, filename)
        with open(filepath, "wb") as f:
            f.write(image_data)

        # Generate thumbnail (~50KB)
        thumbnail_data = compress_image(image_data, max_size_kb=50)
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = os.path.join(task_dir, thumbnail_filename)
        with open(thumbnail_path, "wb") as f:
            f.write(thumbnail_data)

        return filepath

    def _generate_single_image(
        self,
        page: Dict,
        task_id: str,
        reference_image: Optional[bytes] = None,
        retry_count: int = 0,
        full_outline: str = "",
        user_images: Optional[List[bytes]] = None,
        user_topic: str = "",
        image_style: str = "flat"
    ) -> Tuple[int, bool, Optional[str], Optional[str]]:
        """
        Generate single image (with auto retry)

        Args:
            page: Page data
            task_id: Task ID
            reference_image: Reference image (cover image)
            retry_count: Current retry count
            full_outline: Full outline text
            user_images: User uploaded reference images list
            user_topic: User original input
            image_style: Image style (flat, tech, minimal, photo, sketch, infographic, cinematic, brand)

        Returns:
            (index, success, filename, error_message)
        """
        index = page["index"]
        page_type = page["type"]
        page_content = page["content"]

        max_retries = self.AUTO_RETRY_COUNT

        # Get style prompt
        style_prompt = self._get_image_style_prompt(image_style)

        for attempt in range(max_retries):
            try:
                logger.debug(f"Generating image [{index}]: type={page_type}, style={image_style}, attempt={attempt + 1}/{max_retries}")

                # Select template based on config (short prompt or full prompt)
                if self.use_short_prompt and self.prompt_template_short:
                    # Short prompt mode: only page type and content
                    prompt = self.prompt_template_short.format(
                        page_content=page_content,
                        page_type=page_type,
                        image_style=style_prompt
                    )
                    logger.debug(f"  Using short prompt mode ({len(prompt)} chars)")
                else:
                    # Full prompt mode: include outline and user requirements
                    prompt = self.prompt_template.format(
                        page_content=page_content,
                        page_type=page_type,
                        full_outline=full_outline,
                        user_topic=user_topic if user_topic else "Not provided",
                        image_style=style_prompt
                    )

                # Call generator to generate image
                if self.provider_config.get('type') == 'google_genai':
                    logger.debug(f"  Using Google GenAI generator")
                    image_data = self.generator.generate_image(
                        prompt=prompt,
                        aspect_ratio=self.provider_config.get('default_aspect_ratio', '16:9'),
                        temperature=self.provider_config.get('temperature', 1.0),
                        model=self.provider_config.get('model', 'gemini-3-pro-image-preview'),
                        reference_image=reference_image,
                    )
                elif self.provider_config.get('type') == 'image_api':
                    logger.debug(f"  Using Image API generator")
                    # Image API supports multiple reference images
                    # Combine reference images: user uploaded + cover
                    reference_images = []
                    if user_images:
                        reference_images.extend(user_images)
                    if reference_image:
                        reference_images.append(reference_image)

                    image_data = self.generator.generate_image(
                        prompt=prompt,
                        aspect_ratio=self.provider_config.get('default_aspect_ratio', '16:9'),
                        temperature=self.provider_config.get('temperature', 1.0),
                        model=self.provider_config.get('model', 'nano-banana-2'),
                        reference_images=reference_images if reference_images else None,
                    )
                else:
                    logger.debug(f"  Using OpenAI compatible generator")
                    image_data = self.generator.generate_image(
                        prompt=prompt,
                        size=self.provider_config.get('default_size', '1024x1024'),
                        model=self.provider_config.get('model'),
                        quality=self.provider_config.get('quality', 'standard'),
                    )

                # Save image (use current task directory)
                filename = f"{index}.png"
                self._save_image(image_data, filename, self.current_task_dir)
                logger.info(f"[OK] Image [{index}] generated: {filename}")

                return (index, True, filename, None)

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Image [{index}] failed (attempt {attempt + 1}/{max_retries}): {error_msg[:200]}")

                if attempt < max_retries - 1:
                    # Wait and retry
                    wait_time = 2 ** attempt
                    logger.debug(f"  Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue

                logger.error(f"[FAIL] Image [{index}] failed, max retries reached")
                return (index, False, None, error_msg)

        return (index, False, None, "Max retries exceeded")

    def _get_image_style_prompt(self, style: str) -> str:
        """根據圖片風格返回對應的提示詞"""
        style_prompts = {
            'tech': '科技未來風，藍色調，未來感介面、抽象資料流、AI 科技視覺，乾淨背景，霓虹光效果',
            'flat': '扁平插畫風，Flat Design，簡約設計，柔和配色，親和不壓迫，適合教學說明',
            'minimal': '極簡留白風，白色或淺色背景，單一視覺主體，現代感設計，大量留白，高級感',
            'photo': '寫實攝影風，自然光線，真實場景，高品質攝影感，情境感強',
            'sketch': '手繪筆記風，手寫線條插畫，像課堂筆記或白板草圖，親切感，有學習感',
            'infographic': '資訊圖表風，清楚區塊分隔，流程與重點視覺化，結構清楚，適合教學',
            'cinematic': '故事情境風，溫暖光線，有敘事感的場景，像一幕電影畫面，有情緒',
            'brand': '品牌一致風，固定配色與視覺語言，簡潔構圖，專業且可長期使用'
        }
        return style_prompts.get(style, style_prompts['flat'])

    def generate_images(
        self,
        pages: list,
        task_id: str = None,
        full_outline: str = "",
        user_images: Optional[List[bytes]] = None,
        user_topic: str = "",
        image_style: str = "flat"
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generate images (generator, supports SSE streaming)
        Optimized: generate cover first, then concurrent generate other pages

        Args:
            pages: Pages list
            task_id: Task ID (optional)
            full_outline: Full outline text (for style consistency)
            user_images: User uploaded reference images list (optional)
            user_topic: User original input (for intent consistency)
            image_style: Image style (flat, tech, minimal, photo, sketch, infographic, cinematic, brand)

        Yields:
            Progress event dict
        """
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}"

        logger.info(f"Starting image generation task: task_id={task_id}, pages={len(pages)}")

        # Create task directory
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)
        logger.debug(f"Task directory: {self.current_task_dir}")

        total = len(pages)
        generated_images = []
        failed_pages = []
        cover_image_data = None

        # Compress user uploaded reference images to <200KB (reduce memory and transfer overhead)
        compressed_user_images = None
        if user_images:
            compressed_user_images = [compress_image(img, max_size_kb=200) for img in user_images]

        # Initialize task state
        self._task_states[task_id] = {
            "pages": pages,
            "generated": {},
            "failed": {},
            "cover_image": None,
            "full_outline": full_outline,
            "user_images": compressed_user_images,
            "user_topic": user_topic,
            "image_style": image_style
        }

        # ==================== Phase 1: Generate Cover ====================
        cover_page = None
        other_pages = []

        for page in pages:
            if page["type"] == "cover":
                cover_page = page
            else:
                other_pages.append(page)

        # If no cover, use first page as cover
        if cover_page is None and len(pages) > 0:
            cover_page = pages[0]
            other_pages = pages[1:]

        if cover_page:
            # Send cover generation progress
            yield {
                "event": "progress",
                "data": {
                    "index": cover_page["index"],
                    "status": "generating",
                    "message": "Generating cover...",
                    "current": 1,
                    "total": total,
                    "phase": "cover"
                }
            }

            # Generate cover (use user uploaded images as reference)
            index, success, filename, error = self._generate_single_image(
                cover_page, task_id, reference_image=None, full_outline=full_outline,
                user_images=compressed_user_images, user_topic=user_topic,
                image_style=image_style
            )

            if success:
                generated_images.append(filename)
                self._task_states[task_id]["generated"][index] = filename

                # Read cover image as reference, compress to <200KB
                cover_path = os.path.join(self.current_task_dir, filename)
                with open(cover_path, "rb") as f:
                    cover_image_data = f.read()

                # Compress cover image (reduce memory and transfer overhead)
                cover_image_data = compress_image(cover_image_data, max_size_kb=200)
                self._task_states[task_id]["cover_image"] = cover_image_data

                yield {
                    "event": "complete",
                    "data": {
                        "index": index,
                        "status": "done",
                        "image_url": f"/api/images/{task_id}/{filename}",
                        "phase": "cover"
                    }
                }
            else:
                failed_pages.append(cover_page)
                self._task_states[task_id]["failed"][index] = error

                yield {
                    "event": "error",
                    "data": {
                        "index": index,
                        "status": "error",
                        "message": error,
                        "retryable": True,
                        "phase": "cover"
                    }
                }

        # ==================== Phase 2: Generate Other Pages ====================
        if other_pages:
            # Check if high concurrency mode is enabled
            high_concurrency = self.provider_config.get('high_concurrency', False)

            if high_concurrency:
                # High concurrency mode: parallel generation
                yield {
                    "event": "progress",
                    "data": {
                        "status": "batch_start",
                        "message": f"Starting concurrent generation of {len(other_pages)} pages...",
                        "current": len(generated_images),
                        "total": total,
                        "phase": "content"
                    }
                }

                # Use thread pool for concurrent generation
                with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT) as executor:
                    # Submit all tasks
                    future_to_page = {
                        executor.submit(
                            self._generate_single_image,
                            page,
                            task_id,
                            cover_image_data,  # 使用封面作为参考
                            0,  # retry_count
                            full_outline,  # 传入完整大纲
                            compressed_user_images,  # 用户上传的参考图片（已压缩）
                            user_topic,  # 用户原始输入
                            image_style  # 圖片風格
                        ): page
                        for page in other_pages
                    }

                    # Send progress for each page
                    for page in other_pages:
                        yield {
                            "event": "progress",
                            "data": {
                                "index": page["index"],
                                "status": "generating",
                                "current": len(generated_images) + 1,
                                "total": total,
                                "phase": "content"
                            }
                        }

                    # Collect results
                    for future in as_completed(future_to_page):
                        page = future_to_page[future]
                        try:
                            index, success, filename, error = future.result()

                            if success:
                                generated_images.append(filename)
                                self._task_states[task_id]["generated"][index] = filename

                                yield {
                                    "event": "complete",
                                    "data": {
                                        "index": index,
                                        "status": "done",
                                        "image_url": f"/api/images/{task_id}/{filename}",
                                        "phase": "content"
                                    }
                                }
                            else:
                                failed_pages.append(page)
                                self._task_states[task_id]["failed"][index] = error

                                yield {
                                    "event": "error",
                                    "data": {
                                        "index": index,
                                        "status": "error",
                                        "message": error,
                                        "retryable": True,
                                        "phase": "content"
                                    }
                                }

                        except Exception as e:
                            failed_pages.append(page)
                            error_msg = str(e)
                            self._task_states[task_id]["failed"][page["index"]] = error_msg

                            yield {
                                "event": "error",
                                "data": {
                                    "index": page["index"],
                                    "status": "error",
                                    "message": error_msg,
                                    "retryable": True,
                                    "phase": "content"
                                }
                            }
            else:
                # Sequential mode: generate one by one
                yield {
                    "event": "progress",
                    "data": {
                        "status": "batch_start",
                        "message": f"Starting sequential generation of {len(other_pages)} pages...",
                        "current": len(generated_images),
                        "total": total,
                        "phase": "content"
                    }
                }

                for page in other_pages:
                    # Send generation progress
                    yield {
                        "event": "progress",
                        "data": {
                            "index": page["index"],
                            "status": "generating",
                            "current": len(generated_images) + 1,
                            "total": total,
                            "phase": "content"
                        }
                    }

                    # Generate single image
                    index, success, filename, error = self._generate_single_image(
                        page,
                        task_id,
                        cover_image_data,
                        0,
                        full_outline,
                        compressed_user_images,
                        user_topic,
                        image_style
                    )

                    if success:
                        generated_images.append(filename)
                        self._task_states[task_id]["generated"][index] = filename

                        yield {
                            "event": "complete",
                            "data": {
                                "index": index,
                                "status": "done",
                                "image_url": f"/api/images/{task_id}/{filename}",
                                "phase": "content"
                            }
                        }
                    else:
                        failed_pages.append(page)
                        self._task_states[task_id]["failed"][index] = error

                        yield {
                            "event": "error",
                            "data": {
                                "index": index,
                                "status": "error",
                                "message": error,
                                "retryable": True,
                                "phase": "content"
                            }
                        }

        # ==================== Finish ====================
        yield {
            "event": "finish",
            "data": {
                "success": len(failed_pages) == 0,
                "task_id": task_id,
                "images": generated_images,
                "total": total,
                "completed": len(generated_images),
                "failed": len(failed_pages),
                "failed_indices": [p["index"] for p in failed_pages]
            }
        }

    def retry_single_image(
        self,
        task_id: str,
        page: Dict,
        use_reference: bool = True,
        full_outline: str = "",
        user_topic: str = "",
        image_style: str = ""
    ) -> Dict[str, Any]:
        """
        Retry generating single image

        Args:
            task_id: Task ID
            page: Page data
            use_reference: Whether to use cover as reference
            full_outline: Full outline text (from frontend)
            user_topic: User original input (from frontend)
            image_style: Image style (from frontend or task state)

        Returns:
            Generation result
        """
        self.current_task_dir = os.path.join(self.history_root_dir, task_id)
        os.makedirs(self.current_task_dir, exist_ok=True)

        reference_image = None
        user_images = None

        # First try to get context from task state
        if task_id in self._task_states:
            task_state = self._task_states[task_id]
            if use_reference:
                reference_image = task_state.get("cover_image")
            # If no context passed, use task state
            if not full_outline:
                full_outline = task_state.get("full_outline", "")
            if not user_topic:
                user_topic = task_state.get("user_topic", "")
            if not image_style:
                image_style = task_state.get("image_style", "flat")
            user_images = task_state.get("user_images")

        # Default image style if not set
        if not image_style:
            image_style = "flat"

        # If no cover in task state, try to load from file system
        if use_reference and reference_image is None:
            cover_path = os.path.join(self.current_task_dir, "0.png")
            if os.path.exists(cover_path):
                with open(cover_path, "rb") as f:
                    cover_data = f.read()
                # Compress cover to 200KB
                reference_image = compress_image(cover_data, max_size_kb=200)

        index, success, filename, error = self._generate_single_image(
            page,
            task_id,
            reference_image,
            0,
            full_outline,
            user_images,
            user_topic,
            image_style
        )

        if success:
            if task_id in self._task_states:
                self._task_states[task_id]["generated"][index] = filename
                if index in self._task_states[task_id]["failed"]:
                    del self._task_states[task_id]["failed"][index]

            return {
                "success": True,
                "index": index,
                "image_url": f"/api/images/{task_id}/{filename}"
            }
        else:
            return {
                "success": False,
                "index": index,
                "error": error,
                "retryable": True
            }

    def retry_failed_images(
        self,
        task_id: str,
        pages: List[Dict]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Batch retry failed images

        Args:
            task_id: Task ID
            pages: Pages to retry

        Yields:
            Progress events
        """
        # Get reference image and other context from task state
        reference_image = None
        full_outline = ""
        user_images = None
        user_topic = ""
        image_style = "flat"

        if task_id in self._task_states:
            task_state = self._task_states[task_id]
            reference_image = task_state.get("cover_image")
            full_outline = task_state.get("full_outline", "")
            user_images = task_state.get("user_images")
            user_topic = task_state.get("user_topic", "")
            image_style = task_state.get("image_style", "flat")

        total = len(pages)
        success_count = 0
        failed_count = 0

        yield {
            "event": "retry_start",
            "data": {
                "total": total,
                "message": f"Starting retry of {total} failed images"
            }
        }

        with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT) as executor:
            future_to_page = {
                executor.submit(
                    self._generate_single_image,
                    page,
                    task_id,
                    reference_image,
                    0,  # retry_count
                    full_outline,
                    user_images,
                    user_topic,
                    image_style
                ): page
                for page in pages
            }

            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    index, success, filename, error = future.result()

                    if success:
                        success_count += 1
                        if task_id in self._task_states:
                            self._task_states[task_id]["generated"][index] = filename
                            if index in self._task_states[task_id]["failed"]:
                                del self._task_states[task_id]["failed"][index]

                        yield {
                            "event": "complete",
                            "data": {
                                "index": index,
                                "status": "done",
                                "image_url": f"/api/images/{task_id}/{filename}"
                            }
                        }
                    else:
                        failed_count += 1
                        yield {
                            "event": "error",
                            "data": {
                                "index": index,
                                "status": "error",
                                "message": error,
                                "retryable": True
                            }
                        }

                except Exception as e:
                    failed_count += 1
                    yield {
                        "event": "error",
                        "data": {
                            "index": page["index"],
                            "status": "error",
                            "message": str(e),
                            "retryable": True
                        }
                    }

        yield {
            "event": "retry_finish",
            "data": {
                "success": failed_count == 0,
                "total": total,
                "completed": success_count,
                "failed": failed_count
            }
        }

    def regenerate_image(
        self,
        task_id: str,
        page: Dict,
        use_reference: bool = True,
        full_outline: str = "",
        user_topic: str = ""
    ) -> Dict[str, Any]:
        """
        Regenerate image (user triggered, can regenerate even successful ones)

        Args:
            task_id: Task ID
            page: Page data
            use_reference: Whether to use cover as reference
            full_outline: Full outline text
            user_topic: User original input

        Returns:
            Generation result
        """
        return self.retry_single_image(
            task_id, page, use_reference,
            full_outline=full_outline,
            user_topic=user_topic
        )

    def get_image_path(self, task_id: str, filename: str) -> str:
        """
        Get image full path

        Args:
            task_id: Task ID
            filename: File name

        Returns:
            Full path
        """
        task_dir = os.path.join(self.history_root_dir, task_id)
        return os.path.join(task_dir, filename)

    def get_task_state(self, task_id: str) -> Optional[Dict]:
        """Get task state"""
        return self._task_states.get(task_id)

    def cleanup_task(self, task_id: str):
        """Cleanup task state (free memory)"""
        if task_id in self._task_states:
            del self._task_states[task_id]


# Global service instance
_service_instance = None

def get_image_service() -> ImageService:
    """Get global image generation service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ImageService()
    return _service_instance

def reset_image_service():
    """Reset global service instance (call after config update)"""
    global _service_instance
    _service_instance = None
