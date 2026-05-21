"""Gradio 应用界面"""

import json
from pathlib import Path

import gradio as gr
from PIL import Image

from .billing import get_billing_client
from .config import config
from .generator import get_generator
from .prompts import prompt_manager


COPY_PROMPT_JS = """
async (styleName, productDesc, userReq, templatesJson) => {
    if (!styleName) {
        return "⚠️ 请先选择文案类型";
    }

    const templates = JSON.parse(templatesJson || "{}");
    const systemPrompt = templates[styleName];
    if (!systemPrompt) {
        return `❌ 模板「${styleName}」不存在`;
    }

    const formatExamples = (rawPrompt) => {
        const paragraphs = rawPrompt.split("\\n\\n").map((p) => p.trim()).filter(Boolean);
        if (paragraphs.length <= 1) {
            return rawPrompt;
        }

        let formatted = "以下是多个优秀文案示例，请学习其风格和写法：\\n\\n";
        paragraphs.forEach((paragraph, index) => {
            let text = paragraph;
            if (text.startsWith('"') && text.endsWith('"')) {
                text = text.slice(1, -1);
            }
            formatted += `【示例 ${index + 1}】\\n${text}\\n\\n`;
        });
        return formatted.trim();
    };

    const promptText = `你是专业私域朋友圈文案师。
【文案类型】${styleName}

${formatExamples(systemPrompt)}

【商品描述】
${productDesc || "未提供，请以图片信息为主"}

【额外要求】
${userReq || "自然、简短、适合朋友圈"}

请先审核并分析每一张产品图片，再参考上述示例的风格和写法，生成一条全新的朋友圈文案。
输出格式：
【图片分析】
图片1：
- 主体/品类：
- 颜色/材质/款式/细节：
- 可用于文案的卖点/场景：
- 不确定但可能有用的信息：

图片2：
- 主体/品类：
- 颜色/材质/款式/细节：
- 可用于文案的卖点/场景：
- 不确定但可能有用的信息：

如有更多图片，请继续按顺序分析。

【朋友圈文案】
基于图片分析、【商品描述】、【文案类型】、【额外要求】和示例风格，输出一条适合朋友圈发布的新文案。
要求：
1. 必须先输出【图片分析】，再输出【朋友圈文案】
2. 图片分析要具体、简洁，逐张说明，不要合并分析；商品描述可用于补充图片看不清的信息
3. 图片里无法确认、且商品描述也没有提供的品牌、材质、价格、功效，不要当作事实；不确定的信息用“疑似/可能”
4. 朋友圈文案字数不能太长，防止朋友圈折叠显示
5. 不要照搬示例内容，根据【文案类型】、【商品描述】和【额外要求】，生成相似的风格和语气，符合私域营销的风格
6. 不要输出除【图片分析】和【朋友圈文案】之外的多余解释`;

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(promptText);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = promptText;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            const copied = document.execCommand("copy");
            document.body.removeChild(textarea);
            if (!copied) {
                throw new Error("copy failed");
            }
        }
        return "✅ 提示词已复制到剪贴板";
    } catch (error) {
        return "❌ 复制失败，请检查浏览器剪贴板权限";
    }
}
"""


COPY_RESULT_JS = """
async (resultText) => {
    if (!resultText || !resultText.trim()) {
        return "⚠️ 没有可复制的生成结果";
    }

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(resultText);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = resultText;
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            const copied = document.execCommand("copy");
            document.body.removeChild(textarea);
            if (!copied) {
                throw new Error("copy failed");
            }
        }
        return "✅ 生成结果已复制到剪贴板";
    } catch (error) {
        return "❌ 复制失败，请检查浏览器剪贴板权限";
    }
}
"""


DEFAULT_AGENT_STYLE = "上新预告"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def create_app() -> gr.Blocks:
    prompt_choices = prompt_manager.list_all()
    default_wenan_type = prompt_choices[0] if prompt_choices else None
    prompt_templates_json = get_prompt_templates_json()

    with gr.Blocks(title="产品图文案生成器") as demo:
        gr.Markdown(
            """
            # 📝 产品图 → 朋友圈文案生成器
            
            上传产品图片（支持多张），选择文案风格，一键生成适合朋友圈的营销文案。
            """
        )

        with gr.Tabs():
            with gr.TabItem("📝 文案生成"):
                with gr.Row(equal_height=False):
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输入区域")

                        wenan_type = gr.Dropdown(
                            choices=prompt_choices,
                            value=default_wenan_type,
                            label="📝 选择文案类型",
                            interactive=True,
                        )

                        with gr.Group():
                            product_imgs = gr.Files(
                                label="📷 产品图片（可多选）",
                                file_count="multiple",
                                file_types=["image"],
                                height=180,
                            )
                            img_preview = gr.Gallery(
                                label="已上传预览",
                                show_label=True,
                                columns=4,
                                height=150,
                                object_fit="contain",
                                interactive=False,
                            )

                        user_prompt = gr.Textbox(
                            label="🛍️ 商品描述（可选）",
                            lines=3,
                            placeholder="例如：品牌、材质、价格、规格、库存、适用场景、主推卖点...",
                        )
                        user_prompt_extra = gr.Textbox(
                            label="💡 额外要求（可选）",
                            lines=2,
                            placeholder="例如：突出性价比、强调品质、适合送礼...",
                        )
                        with gr.Row():
                            export_prompt_btn = gr.Button("📋 导出提示词", variant="secondary")
                            prompt_copy_status = gr.Textbox(
                                label="提示词状态",
                                interactive=False,
                                scale=2,
                            )
                        reasoning_effort_input = gr.Dropdown(
                            choices=[
                                ("不思考", "minimal"),
                                ("轻", "low"),
                                ("中", "medium"),
                                ("重度", "high"),
                            ],
                            value=config.ARK_REASONING_EFFORT,
                            label="思考程度",
                            info="reasoning_effort：minimal / low / medium / high，默认中度",
                            interactive=True,
                        )
                        generate_btn = gr.Button(
                            "🚀 生成文案",
                            variant="primary",
                        )
                        prompt_templates = gr.Textbox(value=prompt_templates_json, visible=False)

                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 生成结果")
                        output = gr.Textbox(
                            label="文案内容",
                            lines=14,
                            interactive=True,
                        )
                        with gr.Row():
                            copy_result_btn = gr.Button("📋 复制生成结果", variant="secondary")
                            add_to_template_btn = gr.Button("➕ 添加到模板", variant="secondary")
                        result_action_status = gr.Textbox(label="结果操作状态", interactive=False)
                        with gr.Row():
                            token_info = gr.Textbox(
                                label="Token 使用",
                                interactive=False,
                            )
                            img_count = gr.Textbox(
                                label="图片数量",
                                interactive=False,
                                value="0 张",
                            )

            with gr.TabItem("💬 对话生成"):
                agent_style = gr.Dropdown(
                    choices=prompt_choices,
                    value=default_wenan_type,
                    label="文案类型",
                    interactive=True,
                )
                agent_state = gr.State(create_agent_state(default_wenan_type))
                agent_chat = gr.Chatbot(
                    value=create_agent_intro(default_wenan_type),
                    label="对话生成",
                    height=620,
                    show_label=False,
                )
                agent_input = gr.MultimodalTextbox(
                    label="",
                    placeholder="输入需求，或直接上传商品图片...",
                    file_count="multiple",
                    file_types=["image"],
                    lines=2,
                    max_lines=6,
                    submit_btn=True,
                )

            with gr.TabItem("⚙️ 设置"):
                gr.Markdown("### 🔑 API 配置")
                gr.Markdown(f"配置文件路径: `{config.get_env_path()}`")
                
                with gr.Group():
                    api_key_input = gr.Textbox(
                        label="ARK_API_KEY",
                        value=config.ARK_API_KEY,
                        type="password",
                        placeholder="火山引擎 ARK API Key",
                    )
                    model_input = gr.Textbox(
                        label="ARK_MODEL",
                        value=config.ARK_MODEL,
                        placeholder="模型 ID，如: ep-xxxx",
                    )
                    base_url_input = gr.Textbox(
                        label="ARK_BASE_URL",
                        value=config.ARK_BASE_URL,
                        placeholder="API 地址",
                    )
                
                gr.Markdown("### 💳 账单查询配置（可选）")
                with gr.Group():
                    access_key_input = gr.Textbox(
                        label="VOLC_ACCESS_KEY",
                        value=config.VOLC_ACCESS_KEY,
                        type="password",
                        placeholder="火山引擎 Access Key",
                    )
                    secret_key_input = gr.Textbox(
                        label="VOLC_SECRET_KEY",
                        value=config.VOLC_SECRET_KEY,
                        type="password",
                        placeholder="火山引擎 Secret Key",
                    )

                    with gr.Row():
                        balance_btn = gr.Button("💰 查看余额")
                        balance_output = gr.Textbox(label="账户信息", interactive=False, scale=4)
                
                with gr.Row():
                    save_btn = gr.Button("💾 保存配置", variant="primary")
                    config_status = gr.Textbox(label="状态", interactive=False, scale=3)
                
                gr.Markdown("""
                ---
                **说明：**
                - 修改配置后点击「保存配置」即可生效
                - 配置会保存到 `.env` 文件，下次启动自动加载
                - ARK_API_KEY 和 ARK_MODEL 为必填项
                """)

            with gr.TabItem("📋 模板管理"):
                gr.Markdown("### 📝 文案模板管理")
                gr.Markdown(f"模板目录: `{prompt_manager.get_prompts_dir()}`")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        template_list = gr.Dropdown(
                            choices=prompt_manager.list_all(),
                            label="选择模板（自动加载）",
                            interactive=True,
                        )
                        delete_template_btn = gr.Button("🗑️ 删除模板", variant="secondary")
                        
                        gr.Markdown("---")
                        new_template_name = gr.Textbox(
                            label="新模板名称",
                            placeholder="输入模板名称，如：新品上市",
                        )
                        create_template_btn = gr.Button("➕ 创建新模板", variant="primary")
                    
                    with gr.Column(scale=2):
                        template_content = gr.Textbox(
                            label="模板内容",
                            lines=15,
                            placeholder="输入模板示例文案...\n\nAI 会学习这些示例的风格来生成新文案。",
                        )
                        save_template_btn = gr.Button("💾 保存模板", variant="primary")
                        template_status = gr.Textbox(label="状态", interactive=False)
                
                gr.Markdown("""
                ---
                **使用说明：**
                - 选择模板后自动加载内容
                - 模板内容是一些示例文案，AI 会学习这些示例的风格
                - 可以包含多个示例，用空行分隔
                - 创建/修改后，在「文案生成」页面即可选择使用
                """)

        balance_btn.click(
            fn=handle_query_balance,
            inputs=[],
            outputs=balance_output,
        )

        product_imgs.change(
            fn=handle_file_change,
            inputs=product_imgs,
            outputs=[img_preview, img_count],
        )

        generate_btn.click(
            fn=handle_generate,
            inputs=[wenan_type, product_imgs, user_prompt, user_prompt_extra, reasoning_effort_input],
            outputs=[output, token_info],
        )

        export_prompt_btn.click(
            fn=None,
            inputs=[wenan_type, user_prompt, user_prompt_extra, prompt_templates],
            outputs=prompt_copy_status,
            js=COPY_PROMPT_JS,
            show_progress="hidden",
        )

        copy_result_btn.click(
            fn=None,
            inputs=output,
            outputs=result_action_status,
            js=COPY_RESULT_JS,
            show_progress="hidden",
        )

        add_to_template_btn.click(
            fn=handle_add_result_to_template,
            inputs=[wenan_type, output, template_list],
            outputs=[result_action_status, prompt_templates, template_content],
            show_progress="minimal",
        )

        agent_input.submit(
            fn=handle_agent_message,
            inputs=[agent_input, agent_chat, agent_state, agent_style],
            outputs=[agent_input, agent_chat, agent_state],
            show_progress="hidden",
        )

        agent_style.change(
            fn=handle_agent_style_change,
            inputs=agent_style,
            outputs=[agent_chat, agent_state],
            show_progress="hidden",
        )

        save_btn.click(
            fn=handle_save_config,
            inputs=[
                api_key_input,
                model_input,
                base_url_input,
                access_key_input,
                secret_key_input,
            ],
            outputs=config_status,
        )

        template_list.change(
            fn=handle_load_template,
            inputs=template_list,
            outputs=[template_content, template_status],
        )

        save_template_btn.click(
            fn=handle_save_template,
            inputs=[template_list, template_content],
            outputs=[template_status, template_list, wenan_type, prompt_templates],
        )

        create_template_btn.click(
            fn=handle_create_template,
            inputs=[new_template_name],
            outputs=[template_status, template_list, wenan_type, new_template_name, template_content, prompt_templates],
        )

        delete_template_btn.click(
            fn=handle_delete_template,
            inputs=template_list,
            outputs=[template_status, template_list, wenan_type, template_content, prompt_templates],
        )

    return demo


def handle_file_change(filepaths: list[str] | None) -> tuple[list[str], str]:
    if not filepaths:
        return [], "0 张"
    return filepaths, f"{len(filepaths)} 张"


def get_prompt_templates_json() -> str:
    templates = {name: prompt_manager.get(name) or "" for name in prompt_manager.list_all()}
    return json.dumps(templates, ensure_ascii=False)


def create_agent_state(style_name: str | None = None) -> dict:
    if not style_name:
        style_name = DEFAULT_AGENT_STYLE if DEFAULT_AGENT_STYLE in prompt_manager.list_all() else ""
    if not style_name and prompt_manager.list_all():
        style_name = prompt_manager.list_all()[0]
    return {
        "style_name": style_name,
        "images": [],
        "fields": {},
        "requirements": analyze_agent_requirements(style_name),
        "pending": "",
        "generated": "",
    }


def create_agent_intro(style_name: str | None) -> list[dict]:
    state = create_agent_state(style_name)
    requirements = state.get("requirements") or []
    required_labels = "、".join(field["label"] for field in requirements) or "商品信息"
    content = (
        f"已选择「{state.get('style_name') or '未选择'}」。我会先读取这个类型的历史文案，"
        f"再判断需要你提供哪些信息。\n\n"
        f"根据当前模板，可能需要：{required_labels}。\n\n"
        "请先发送商品图片，也可以同时补充你已经知道的商品信息。"
    )
    return [{"role": "assistant", "content": content}]


def _extract_agent_text(message) -> str:
    if isinstance(message, dict):
        return (message.get("text") or "").strip()
    return str(message or "").strip()


def _extract_agent_files(message) -> list[str]:
    if not isinstance(message, dict):
        return []

    paths = []
    for file_obj in message.get("files") or []:
        path = None
        if isinstance(file_obj, str):
            path = file_obj
        elif isinstance(file_obj, dict):
            path = file_obj.get("path") or file_obj.get("name")
        else:
            path = getattr(file_obj, "path", None) or getattr(file_obj, "name", None)

        if path and Path(path).suffix.lower() in IMAGE_EXTENSIONS:
            paths.append(path)
    return paths


def _format_agent_user_message(text: str, files: list[str]) -> str:
    parts = []
    if files:
        parts.append(f"已上传 {len(files)} 张图片")
    if text:
        parts.append(text)
    return "\n\n".join(parts) or "（空消息）"


def _append_agent_message(history: list[dict], role: str, content: str) -> list[dict]:
    history.append({"role": role, "content": content})
    return history


def analyze_agent_requirements(style_name: str | None) -> list[dict]:
    template = prompt_manager.get(style_name or "") or ""
    text = f"{style_name or ''}\n{template}"
    requirements = [
        {
            "key": "product_desc",
            "label": "商品细节",
            "question": "请补充商品细节，比如品牌、材质、价格、规格、库存、主推卖点。",
        }
    ]

    if any(keyword in text for keyword in ["点", "下午", "上午", "明天", "今天", "开团", "上好闹钟", "预告", "上新"]):
        requirements.append(
            {
                "key": "launch_time",
                "label": "上新时间",
                "question": "历史文案里很重视上新/开团时间。这次上新时间是何时？",
            }
        )

    if any(keyword in text for keyword in ["数量", "库存", "限量", "不到", "只有", "手慢", "抢", "无补", "且买且珍惜"]):
        requirements.append(
            {
                "key": "inventory",
                "label": "库存/稀缺信息",
                "question": "这个类型常用稀缺感。库存、数量或补货情况是什么？不强调稀缺也可以回复“不强调”。",
            }
        )

    if any(keyword in text for keyword in ["礼物", "送礼", "母亲节", "七夕", "生日", "节日"]):
        requirements.append(
            {
                "key": "occasion",
                "label": "送礼/使用场景",
                "question": "这次适合什么场景？比如送礼、通勤、约会、旅行、节日。",
            }
        )

    if any(keyword in text for keyword in ["好评", "买家秀", "反馈", "回购", "评价", "夸"]):
        requirements.append(
            {
                "key": "feedback",
                "label": "用户反馈",
                "question": "这个类型需要真实感。有没有买家反馈、试穿体验或想强调的使用感受？",
            }
        )

    if any(keyword in text for keyword in ["群", "拉群", "进群", "催单", "截单", "付款", "接龙"]):
        requirements.append(
            {
                "key": "action",
                "label": "行动方式",
                "question": "用户需要怎么行动？比如进群、接龙、私信、付款截止时间。",
            }
        )

    return requirements


def _wants_agent_generate(text: str) -> bool:
    normalized = text.strip().lower()
    return any(word in normalized for word in ["生成", "直接生成", "开始", "go"]) or normalized in {"没有", "无", "不用", "不补充"}


def _wants_agent_save(text: str) -> bool:
    return "保存" in text and "模板" in text


def _extract_final_copy(text: str) -> str:
    marker = "【朋友圈文案】"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def _collect_agent_field(text: str, state: dict) -> None:
    if not text:
        return

    pending = state.get("pending")
    fields = state.setdefault("fields", {})
    if pending == "images":
        if text.strip() not in {"已上传", "图片"}:
            fields["product_desc"] = text
    elif pending:
        fields[pending] = text
    elif not fields.get("product_desc"):
        fields["product_desc"] = text
    else:
        fields["extra"] = text

    state["pending"] = ""


def _next_agent_question(state: dict) -> str | None:
    if not state.get("images"):
        state["pending"] = "images"
        return "请先上传商品图片。可以一次发多张，我会逐张分析。"

    fields = state.setdefault("fields", {})
    for field in state.get("requirements") or []:
        if not fields.get(field["key"]):
            state["pending"] = field["key"]
            return field["question"]

    return None


def _build_agent_extra(state: dict) -> str:
    parts = []
    fields = state.get("fields") or {}
    for field in state.get("requirements") or []:
        value = fields.get(field["key"])
        if value:
            parts.append(f"{field['label']}：{value}")
    if fields.get("extra"):
        parts.append(fields["extra"])
    return "\n".join(parts) or "自然、简短、适合朋友圈"


def _build_agent_product_desc(state: dict) -> str:
    fields = state.get("fields") or {}
    return fields.get("product_desc") or "未提供，请以图片信息为主"


def handle_agent_style_change(style_name: str | None) -> tuple[list[dict], dict]:
    return create_agent_intro(style_name), create_agent_state(style_name)


def handle_agent_message(message, history: list[dict] | None, state: dict | None, style_name: str | None):
    history = history or []
    state = state or create_agent_state(style_name)
    if style_name and state.get("style_name") != style_name:
        state = create_agent_state(style_name)
    text = _extract_agent_text(message)
    files = _extract_agent_files(message)

    if not text and not files:
        yield gr.MultimodalTextbox(value=None), history, state
        return

    state["images"].extend(files)
    history = _append_agent_message(history, "user", _format_agent_user_message(text, files))
    yield gr.MultimodalTextbox(value=None), history, state

    if "重来" in text or "重新开始" in text:
        state = create_agent_state(style_name)
        history = create_agent_intro(style_name)
        yield gr.MultimodalTextbox(value=None), history, state
        return

    if _wants_agent_save(text) and state.get("generated"):
        history = _append_agent_message(history, "assistant", "💾 正在保存到历史文案模板...")
        yield gr.MultimodalTextbox(value=None), history, state
        saved_copy = _extract_final_copy(state["generated"])
        status, _, _ = handle_add_result_to_template(state.get("style_name"), saved_copy, state.get("style_name"))
        history = _append_agent_message(history, "assistant", status)
        yield gr.MultimodalTextbox(value=None), history, state
        return

    if text.strip() not in {"生成", "直接生成", "开始", "go", "没有", "无", "不用", "不补充"}:
        _collect_agent_field(text, state)
    question = _next_agent_question(state)
    if question and not _wants_agent_generate(text):
        history = _append_agent_message(history, "assistant", question)
        yield gr.MultimodalTextbox(value=None), history, state
        return

    try:
        config.validate()
    except ValueError as e:
        history = _append_agent_message(history, "assistant", f"⚠️ {e}\n请先到「设置」页配置 API Key 和模型。")
        yield gr.MultimodalTextbox(value=None), history, state
        return

    if not state.get("style_name"):
        history = _append_agent_message(history, "assistant", "还没有可用的文案模板。请先到「模板管理」里创建一个模板。")
        yield gr.MultimodalTextbox(value=None), history, state
        return

    history = _append_agent_message(history, "assistant", "📚 正在分析历史文案，判断这个类型需要哪些信息...")
    yield gr.MultimodalTextbox(value=None), history, state

    history = _append_agent_message(history, "assistant", "🔎 正在分析图片...")
    yield gr.MultimodalTextbox(value=None), history, state

    history = _append_agent_message(history, "assistant", "✍️ 正在生成朋友圈文案...")
    yield gr.MultimodalTextbox(value=None), history, state

    images = [Image.open(path) for path in state["images"]]
    result = get_generator().generate(
        state["style_name"],
        images,
        _build_agent_product_desc(state),
        _build_agent_extra(state),
        config.ARK_REASONING_EFFORT,
    )

    if result.error:
        history = _append_agent_message(history, "assistant", result.error)
        yield gr.MultimodalTextbox(value=None), history, state
        return

    state["generated"] = result.content
    final_copy = _extract_final_copy(result.content)
    history = _append_agent_message(
        history,
        "assistant",
        final_copy,
    )
    yield gr.MultimodalTextbox(value=None), history, state


def handle_save_config(
    api_key: str,
    model: str,
    base_url: str,
    access_key: str,
    secret_key: str,
) -> str:
    if not api_key or not model:
        return "❌ ARK_API_KEY 和 ARK_MODEL 为必填项"
    
    config.update(
        ARK_API_KEY=api_key,
        ARK_MODEL=model,
        ARK_BASE_URL=base_url,
        VOLC_ACCESS_KEY=access_key,
        VOLC_SECRET_KEY=secret_key,
    )
    
    try:
        config.save_to_env()
        return f"✅ 配置已保存到: {config.get_env_path()}"
    except Exception as e:
        return f"❌ 保存失败: {str(e)}"


def handle_query_balance() -> str:
    try:
        config.validate_billing()
    except ValueError as e:
        return f"⚠️ {str(e)}"

    client = get_billing_client()
    data = client.query_balance()
    return client.format_balance(data)


def handle_load_template(name: str) -> tuple[str, str]:
    if not name:
        return "", ""
    content = prompt_manager.get(name)
    if content is None:
        return "", f"❌ 模板「{name}」不存在"
    return content, f"✅ 已加载模板「{name}」"


def handle_add_result_to_template(
    wenan_type: str | None,
    result_text: str | None,
    selected_template: str | None,
) -> tuple[str, str, object]:
    if not wenan_type:
        return "⚠️ 请先选择文案类型", get_prompt_templates_json(), gr.update()

    text = (result_text or "").strip()
    if not text:
        return "⚠️ 没有可添加的生成结果", get_prompt_templates_json(), gr.update()

    current_template = prompt_manager.get(wenan_type)
    if current_template is None:
        return f"❌ 模板「{wenan_type}」不存在", get_prompt_templates_json(), gr.update()

    updated_template = f"{current_template.rstrip()}\n\n{text}" if current_template.strip() else text
    if not prompt_manager.save(wenan_type, updated_template):
        return "❌ 添加失败", get_prompt_templates_json(), gr.update()

    template_content_update = updated_template if selected_template == wenan_type else gr.update()
    return f"✅ 已添加到模板「{wenan_type}」", get_prompt_templates_json(), template_content_update


def handle_save_template(name: str, content: str) -> tuple[str, gr.Dropdown, gr.Dropdown, str]:
    if not name:
        return "❌ 请先选择或创建模板", gr.Dropdown(), gr.Dropdown(), get_prompt_templates_json()
    if not content.strip():
        return "❌ 模板内容不能为空", gr.Dropdown(), gr.Dropdown(), get_prompt_templates_json()
    
    if prompt_manager.save(name, content):
        choices = prompt_manager.list_all()
        return (
            f"✅ 模板「{name}」已保存",
            gr.Dropdown(choices=choices),
            gr.Dropdown(choices=choices),
            get_prompt_templates_json(),
        )
    return "❌ 保存失败", gr.Dropdown(), gr.Dropdown(), get_prompt_templates_json()


def handle_create_template(name: str) -> tuple[str, gr.Dropdown, gr.Dropdown, str, str, str]:
    if not name:
        return "❌ 请输入模板名称", gr.Dropdown(), gr.Dropdown(), "", "", get_prompt_templates_json()
    if name in prompt_manager.list_all():
        return f"❌ 模板「{name}」已存在", gr.Dropdown(), gr.Dropdown(), "", "", get_prompt_templates_json()
    
    if prompt_manager.save(name, ""):
        choices = prompt_manager.list_all()
        return (
            f"✅ 模板「{name}」已创建，请编辑内容",
            gr.Dropdown(choices=choices),
            gr.Dropdown(choices=choices),
            "",
            "",
            get_prompt_templates_json(),
        )
    return "❌ 创建失败", gr.Dropdown(), gr.Dropdown(), "", "", get_prompt_templates_json()


def handle_delete_template(name: str) -> tuple[str, gr.Dropdown, gr.Dropdown, str, str]:
    if not name:
        return "❌ 请选择要删除的模板", gr.Dropdown(), gr.Dropdown(), "", get_prompt_templates_json()
    
    if prompt_manager.delete(name):
        choices = prompt_manager.list_all()
        return (
            f"✅ 模板「{name}」已删除",
            gr.Dropdown(choices=choices),
            gr.Dropdown(choices=choices),
            "",
            get_prompt_templates_json(),
        )
    return "❌ 删除失败", gr.Dropdown(), gr.Dropdown(), "", get_prompt_templates_json()


def handle_generate(
    wenan_type: str,
    product_imgs: list[str] | None,
    product_desc: str | None,
    user_prompt: str | None,
    reasoning_effort: str | None,
) -> tuple[str, str]:
    try:
        config.validate()
    except ValueError as e:
        return f"⚠️ {e}\n请在「设置」标签页中配置", ""
    
    if not wenan_type:
        return "⚠️ 请选择文案类型", ""
    if not product_imgs:
        return "⚠️ 请上传至少一张产品图片", ""

    images = [Image.open(path) for path in product_imgs]

    gen = get_generator()
    result = gen.generate(wenan_type, images, product_desc, user_prompt, reasoning_effort)

    if result.error:
        return result.error, ""

    token_text = f"输入: {result.prompt_tokens} | 输出: {result.completion_tokens} | 总计: {result.total_tokens}"
    return result.content, token_text


def main() -> None:
    try:
        config.validate()
    except ValueError as e:
        print(f"警告: {e}")
        print("请在「设置」标签页中配置 API Key")

    if not prompt_manager.list_all():
        print("警告: prompts 文件夹为空，请添加模板文件")

    demo = create_app()
    demo.queue().launch(
        server_name=config.SERVER_HOST,
        server_port=config.SERVER_PORT,
    )


if __name__ == "__main__":
    main()
