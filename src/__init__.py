"""产品图文案生成器"""

from .config import config
from .generator import get_generator
from .prompts import prompt_manager

__all__ = ["config", "get_generator", "prompt_manager"]
