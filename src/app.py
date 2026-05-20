"""Gradio 应用界面"""

import gradio as gr
from PIL import Image

from .billing import get_billing_client
from .config import config
from .exporter import export_to_docx
from .generator import get_generator
from .prompts import prompt_manager


def create_app() -> gr.Blocks:
    with gr.Blocks(title="产品图文案生成器") as demo:
        gr.Markdown(
            """
            # 📝 产品图 → 朋友圈文案生成器
            
            上传产品图片（支持多张），选择文案风格，一键生成适合朋友圈的营销文案。
            """
        )

        with gr.Tabs():
            with gr.TabItem("📝 文案生成"):
                with gr.Row():
                    balance_btn = gr.Button("💰 查询账户余额")
                    balance_output = gr.Textbox(label="账户信息", interactive=False, scale=4)

                gr.Markdown("---")

                with gr.Row(equal_height=False):
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 输入区域")
                        
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
                        
                        wenan_type = gr.Dropdown(
                            choices=prompt_manager.list_all(),
                            label="📝 选择文案类型",
                            interactive=True,
                        )
                        user_prompt = gr.Textbox(
                            label="💡 额外要求（可选）",
                            lines=2,
                            placeholder="例如：突出性价比、强调品质、适合送礼...",
                        )
                        generate_btn = gr.Button(
                            "🚀 生成文案",
                            variant="primary",
                        )

                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 生成结果")
                        output = gr.Textbox(
                            label="文案内容",
                            lines=14,
                        )
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
                        export_btn = gr.Button("📥 导出 Word", variant="secondary")
                        export_status = gr.Textbox(label="导出状态", interactive=False)
                        saved_prompt = gr.Textbox(visible=False)

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
            inputs=[wenan_type, product_imgs, user_prompt],
            outputs=[output, token_info, saved_prompt],
        )

        export_btn.click(
            fn=handle_export,
            inputs=[product_imgs, saved_prompt],
            outputs=export_status,
        )

        save_btn.click(
            fn=handle_save_config,
            inputs=[api_key_input, model_input, base_url_input, access_key_input, secret_key_input],
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
            outputs=[template_status, template_list, wenan_type],
        )

        create_template_btn.click(
            fn=handle_create_template,
            inputs=[new_template_name],
            outputs=[template_status, template_list, wenan_type, new_template_name, template_content],
        )

        delete_template_btn.click(
            fn=handle_delete_template,
            inputs=template_list,
            outputs=[template_status, template_list, wenan_type, template_content],
        )

    return demo


def handle_file_change(filepaths: list[str] | None) -> tuple[list[str], str]:
    if not filepaths:
        return [], "0 张"
    return filepaths, f"{len(filepaths)} 张"


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


def handle_save_template(name: str, content: str) -> tuple[str, gr.Dropdown, gr.Dropdown]:
    if not name:
        return "❌ 请先选择或创建模板", gr.Dropdown(), gr.Dropdown()
    if not content.strip():
        return "❌ 模板内容不能为空", gr.Dropdown(), gr.Dropdown()
    
    if prompt_manager.save(name, content):
        choices = prompt_manager.list_all()
        return f"✅ 模板「{name}」已保存", gr.Dropdown(choices=choices), gr.Dropdown(choices=choices)
    return "❌ 保存失败", gr.Dropdown(), gr.Dropdown()


def handle_create_template(name: str) -> tuple[str, gr.Dropdown, gr.Dropdown, str, str]:
    if not name:
        return "❌ 请输入模板名称", gr.Dropdown(), gr.Dropdown(), "", ""
    if name in prompt_manager.list_all():
        return f"❌ 模板「{name}」已存在", gr.Dropdown(), gr.Dropdown(), "", ""
    
    if prompt_manager.save(name, ""):
        choices = prompt_manager.list_all()
        return f"✅ 模板「{name}」已创建，请编辑内容", gr.Dropdown(choices=choices), gr.Dropdown(choices=choices), "", ""
    return "❌ 创建失败", gr.Dropdown(), gr.Dropdown(), "", ""


def handle_delete_template(name: str) -> tuple[str, gr.Dropdown, gr.Dropdown, str]:
    if not name:
        return "❌ 请选择要删除的模板", gr.Dropdown(), gr.Dropdown(), ""
    
    if prompt_manager.delete(name):
        choices = prompt_manager.list_all()
        return f"✅ 模板「{name}」已删除", gr.Dropdown(choices=choices), gr.Dropdown(choices=choices), ""
    return "❌ 删除失败", gr.Dropdown(), gr.Dropdown(), ""


def handle_generate(
    wenan_type: str, product_imgs: list[str] | None, user_prompt: str | None
) -> tuple[str, str, str]:
    try:
        config.validate()
    except ValueError as e:
        return f"⚠️ {e}\n请在「设置」标签页中配置", "", ""
    
    if not wenan_type:
        return "⚠️ 请选择文案类型", "", ""
    if not product_imgs:
        return "⚠️ 请上传至少一张产品图片", "", ""

    images = [Image.open(path) for path in product_imgs]

    gen = get_generator()
    result = gen.generate(wenan_type, images, user_prompt)

    if result.error:
        return result.error, "", ""

    token_text = f"输入: {result.prompt_tokens} | 输出: {result.completion_tokens} | 总计: {result.total_tokens}"
    return result.content, token_text, result.prompt


def handle_export(
    images: list[str] | None,
    prompt: str,
) -> str:
    if not images and not prompt:
        return "❌ 没有可导出的内容"
    
    try:
        output_path = export_to_docx(images, prompt)
        return f"✅ 已导出: {output_path}"
    except Exception as e:
        return f"❌ 导出失败: {str(e)}"


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
