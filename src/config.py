"""配置管理模块 - 从环境变量加载敏感配置"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    _app_dir = Path(sys.executable).parent
else:
    _app_dir = Path(__file__).parent.parent

_env_path = _app_dir / ".env"

if not _env_path.exists():
    _env_path.write_text(
        "# 火山引擎 API 配置\n"
        "# 请在 UI 的「设置」标签页中配置\n"
        "\n"
        "ARK_API_KEY=\n"
        "ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3\n"
        "ARK_MODEL=\n"
        "\n"
        "# 火山引擎账单查询配置（可选）\n"
        "VOLC_ACCESS_KEY=\n"
        "VOLC_SECRET_KEY=\n"
        "\n"
        "# 服务器配置\n"
        "SERVER_HOST=0.0.0.0\n"
        "SERVER_PORT=7860\n",
        encoding="utf-8",
    )

load_dotenv(_env_path)


class Config:
    ARK_API_KEY: str = os.getenv("ARK_API_KEY", "")
    ARK_BASE_URL: str = os.getenv(
        "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
    )
    ARK_MODEL: str = os.getenv("ARK_MODEL", "")
    VOLC_ACCESS_KEY: str = os.getenv("VOLC_ACCESS_KEY", "")
    VOLC_SECRET_KEY: str = os.getenv("VOLC_SECRET_KEY", "")
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "7860"))

    @classmethod
    def validate(cls) -> None:
        missing = []
        if not cls.ARK_API_KEY:
            missing.append("ARK_API_KEY")
        if not cls.ARK_MODEL:
            missing.append("ARK_MODEL")

        if missing:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing)}，请检查 .env 文件")

    @classmethod
    def validate_billing(cls) -> None:
        missing = []
        if not cls.VOLC_ACCESS_KEY:
            missing.append("VOLC_ACCESS_KEY")
        if not cls.VOLC_SECRET_KEY:
            missing.append("VOLC_SECRET_KEY")

        if missing:
            raise ValueError(f"缺少账单查询所需的环境变量: {', '.join(missing)}")

    @classmethod
    def update(cls, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(cls, key) and value:
                setattr(cls, key, value)

    @classmethod
    def save_to_env(cls) -> None:
        global _env_path
        lines = [
            f"# 火山引擎 API 配置",
            f"# 自动生成于配置保存",
            f"",
            f"ARK_API_KEY={cls.ARK_API_KEY}",
            f"ARK_BASE_URL={cls.ARK_BASE_URL}",
            f"ARK_MODEL={cls.ARK_MODEL}",
            f"",
            f"# 火山引擎账单查询配置（可选）",
            f"VOLC_ACCESS_KEY={cls.VOLC_ACCESS_KEY}",
            f"VOLC_SECRET_KEY={cls.VOLC_SECRET_KEY}",
            f"",
            f"# 服务器配置",
            f"SERVER_HOST={cls.SERVER_HOST}",
            f"SERVER_PORT={cls.SERVER_PORT}",
        ]
        _env_path.write_text("\n".join(lines), encoding="utf-8")

    @classmethod
    def get_env_path(cls) -> str:
        if getattr(sys, "frozen", False):
            return "程序所在目录\\.env"
        return str(_env_path)


config = Config()
