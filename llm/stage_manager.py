import yaml
from pathlib import Path


class StageManager:
    """
    面试阶段状态机。
    按 interview.yaml 中定义的顺序推进阶段，每阶段轮次达到 max_turns 后自动推进。
    """

    def __init__(self, scene_path: str | Path):
        with open(scene_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.stage_order: list[str] = self.config["stage_order"]
        self.stages: dict = self.config["stages"]
        self.system_base: str = self.config.get("system_base", "")

        self._stage_index: int = 0
        self._turn_count: int = 0  # 当前阶段已完成的轮次数

    # ── 只读属性 ──────────────────────────────────────────

    @property
    def current_stage_name(self) -> str:
        if self._stage_index < len(self.stage_order):
            return self.stage_order[self._stage_index]
        return "closing"

    @property
    def current_stage_config(self) -> dict:
        return self.stages.get(self.current_stage_name, {})

    @property
    def current_stage_label(self) -> str:
        """返回阶段中文名，供前端展示。"""
        return self.current_stage_config.get("name", self.current_stage_name)

    @property
    def is_finished(self) -> bool:
        return self._stage_index >= len(self.stage_order)

    @property
    def turn_count(self) -> int:
        return self._turn_count

    # ── 核心方法 ──────────────────────────────────────────

    def get_opening_line(self) -> str:
        """返回当前阶段的开场白。"""
        return self.current_stage_config.get("opening_line", "")

    def get_system_prompt(self) -> str:
        """返回当前阶段完整的 system prompt（base + stage）。"""
        stage_prompt = self.current_stage_config.get("stage_prompt", "")
        return f"{self.system_base}\n\n{stage_prompt}".strip()

    def record_turn(self) -> bool:
        """
        记录一轮用户发言已完成。
        返回 True 表示当前阶段已满 max_turns，调用方应调用 advance()。
        """
        self._turn_count += 1
        max_turns = self.current_stage_config.get("max_turns", 999)
        return self._turn_count >= max_turns

    def advance(self) -> tuple[bool, str]:
        """
        推进到下一阶段。
        返回 (是否推进成功, 新阶段名称)。
        推进成功后调用 get_opening_line() 获取新阶段开场白。
        """
        if self._stage_index + 1 < len(self.stage_order):
            self._stage_index += 1
            self._turn_count = 0
            return True, self.current_stage_name
        # 已到最后阶段
        self._stage_index = len(self.stage_order)  # 标记为 finished
        return False, "closing"

    def stage_progress(self) -> dict:
        """返回当前进度信息，供前端渲染阶段进度条。"""
        return {
            "stage_order": self.stage_order,
            "current_stage": self.current_stage_name,
            "current_index": self._stage_index,
            "turn_count": self._turn_count,
            "max_turns": self.current_stage_config.get("max_turns", 0),
            "is_finished": self.is_finished,
        }
