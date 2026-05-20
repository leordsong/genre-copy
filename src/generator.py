"""文案生成核心模块"""

import base64
from dataclasses import dataclass

from PIL import Image
from volcenginesdkarkruntime import Ark

from .config import config
from .prompts import prompt_manager


@dataclass
class GenerateResult:
    content: str
    prompt: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: str = ""


class ContentGenerator:
    def __init__(self) -> None:
        self.client = Ark(
            base_url=config.ARK_BASE_URL,
            api_key=config.ARK_API_KEY,
        )
        self.temperature = 0.7
        self.max_tokens = 1024

    def _image_to_base64(self, image: Image.Image) -> str:
        import io
        buffer = io.BytesIO()
        image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()

    def _format_examples(self, raw_prompt: str) -> str:
        paragraphs = [p.strip() for p in raw_prompt.split("\n\n") if p.strip()]
        if len(paragraphs) <= 1:
            return raw_prompt

        formatted = "以下是多个优秀文案示例，请学习其风格和写法：\n\n"
        for i, p in enumerate(paragraphs, 1):
            if p.startswith('"') and p.endswith('"'):
                p = p[1:-1]
            formatted += f"【示例 {i}】\n{p}\n\n"
        return formatted.strip()

    def _build_content(
        self, style_name: str, system_prompt: str, user_req: str, images_b64: list[str]
    ) -> tuple[list, str]:
        formatted_prompt = self._format_examples(system_prompt)
        content = []

        for image_b64 in images_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                }
            )

        prompt_text = f"""你是专业私域朋友圈文案师。
【文案类型】{style_name}

{formatted_prompt}

【额外要求】
{user_req}

请根据产品图片，参考上述示例的风格和写法，生成一条全新的朋友圈文案。
要求：
1. 字数不能太长，防止朋友圈折叠显示
2. 不要照搬示例内容，根据【文案类型】和【额外要求】，生成相似的风格和语气，符合私域营销的风格
3. 直接输出文案，不要有多余解释"""

        content.append(
            {
                "type": "text",
                "text": prompt_text,
            }
        )

        return content, prompt_text

    def _print_request(self, messages: list, images_b64: list[str]) -> None:
        print("\n" + "=" * 60)
        print("【请求参数】")
        print(f"Model: {config.ARK_MODEL}")
        print(f"Temperature: {self.temperature}")
        print(f"Max Tokens: {self.max_tokens}")
        print(f"图片数量: {len(images_b64)}")
        print("\n【Messages 内容】")
        for msg in messages:
            print(f"Role: {msg['role']}")
            for i, item in enumerate(msg["content"]):
                if item["type"] == "text":
                    print(f"Text (前200字): {item['text'][:200]}...")
                elif item["type"] == "image_url":
                    b64_preview = item["image_url"]["url"].split(",")[1][:50]
                    print(f"Image {i+1} base64 (前50字): {b64_preview}...")
        print("=" * 60 + "\n")

    def _print_response(self, completion) -> None:
        print("\n" + "=" * 60)
        print("【响应结果】")
        print(f"ID: {completion.id}")
        print(f"Model: {completion.model}")
        print(f"Created: {completion.created}")
        print(f"\n【Usage】")
        print(f"Prompt Tokens: {completion.usage.prompt_tokens}")
        print(f"Completion Tokens: {completion.usage.completion_tokens}")
        print(f"Total Tokens: {completion.usage.total_tokens}")
        print(f"\n【生成内容】")
        print(completion.choices[0].message.content)
        print("=" * 60 + "\n")

    def generate(
        self,
        wenan_type: str,
        product_imgs: list[Image.Image],
        user_prompt: str | None = None,
    ) -> GenerateResult:
        system_prompt = prompt_manager.get(wenan_type)
        if system_prompt is None:
            return GenerateResult(content="", error=f"未找到文案类型: {wenan_type}")

        if not product_imgs:
            return GenerateResult(content="", error="请上传至少一张产品图片")

        user_req = user_prompt or "自然、简短、适合朋友圈"
        images_b64 = [self._image_to_base64(img) for img in product_imgs]
        content, prompt_text = self._build_content(wenan_type, system_prompt, user_req, images_b64)

        messages = [{"role": "user", "content": content}]

        self._print_request(messages, images_b64)

        try:
            completion = self.client.chat.completions.create(
                model=config.ARK_MODEL,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            self._print_response(completion)

            usage = completion.usage
            return GenerateResult(
                content=completion.choices[0].message.content.strip(),
                prompt=prompt_text,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )
        except Exception as e:
            print(f"\n【错误】{str(e)}\n")
            return GenerateResult(content="", error=f"错误: {str(e)}")


generator: ContentGenerator | None = None
_last_api_key: str = ""
_last_base_url: str = ""


def get_generator() -> ContentGenerator:
    global generator, _last_api_key, _last_base_url
    from .config import config
    
    if generator is None or _last_api_key != config.ARK_API_KEY or _last_base_url != config.ARK_BASE_URL:
        generator = ContentGenerator()
        _last_api_key = config.ARK_API_KEY
        _last_base_url = config.ARK_BASE_URL
    return generator
