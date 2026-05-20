"""Prompts 模板加载模块"""

import sys
from pathlib import Path


def _get_prompts_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        user_prompts = exe_dir / "prompts"
        if not user_prompts.exists():
            user_prompts.mkdir(parents=True, exist_ok=True)
        return user_prompts
    return Path(__file__).parent.parent / "prompts"


class PromptManager:
    def __init__(self, prompts_dir: Path | None = None):
        if prompts_dir is None:
            prompts_dir = _get_prompts_dir()
        self.prompts_dir = prompts_dir
        self._prompts: dict[str, str] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.prompts_dir.exists():
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            return

        for f in self.prompts_dir.glob("*.txt"):
            name = f.stem
            self._prompts[name] = f.read_text(encoding="utf-8").strip()

    def get(self, name: str) -> str | None:
        return self._prompts.get(name)

    def list_all(self) -> list[str]:
        return list(self._prompts.keys())

    def reload(self) -> None:
        self._prompts.clear()
        self._load_all()

    def save(self, name: str, content: str) -> bool:
        try:
            filepath = self.prompts_dir / f"{name}.txt"
            filepath.write_text(content.strip(), encoding="utf-8")
            self._prompts[name] = content.strip()
            return True
        except Exception:
            return False

    def delete(self, name: str) -> bool:
        try:
            filepath = self.prompts_dir / f"{name}.txt"
            if filepath.exists():
                filepath.unlink()
            if name in self._prompts:
                del self._prompts[name]
            return True
        except Exception:
            return False

    def get_prompts_dir(self) -> str:
        if getattr(sys, "frozen", False):
            return "程序所在目录\\prompts"
        return str(self.prompts_dir)


prompt_manager = PromptManager()
