"""
Session Memory — 单次会话内的记忆管理

解决的核心问题：
  对话历史（history）只是原始文本序列，无法快速回答：
    - "用户最近提到的订单号是什么？"
    - "这是用户第几次投诉？"
    - "用户偏好什么品类？"

  SessionMemory 在对话历史之上维护结构化摘要，
  让 Agent 能直接读取，而不是每次都扫描全部历史。

作用域：单次会话（进程内）。
跨会话持久化见 TODO 注释，留给模块 3 扩展。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserProfile:
    """从对话中动态提取的用户画像"""
    # 本次会话中确认过的订单号列表（按提及顺序）
    mentioned_order_ids: list[str] = field(default_factory=list)
    # 提及过的商品名
    mentioned_products: list[str] = field(default_factory=list)
    # 投诉次数（用于路由决策：超过 2 次自动转人工）
    complaint_count: int = 0
    # 最近一次的主意图（用于短句指代消解）
    last_intent: Optional[str] = None
    # 最近一次的 slots（"就退那个" → 直接复用）
    last_slots: dict = field(default_factory=dict)


class SessionMemory:
    """
    会话记忆管理器。

    设计决策：
      - 不替换 history 列表，而是作为独立的结构化索引
      - Agent 更新 memory，意图分类器从 memory 读上下文
      - update() 在每轮 Agent 处理完成后调用（非侵入式）

    用法：
        memory = SessionMemory()
        memory.update(intent_result, user_message)
        print(memory.profile.last_intent)
        ctx = memory.build_context_hint()   # 注入给意图分类器
    """

    def __init__(self):
        self.profile = UserProfile()

    def update(self, intent_result, user_message: str) -> None:
        """
        每轮对话结束后调用，更新结构化摘要。

        Args:
            intent_result: IntentResult（来自 classifier）
            user_message:  原始用户消息
        """
        # 更新最近意图 / 槽位（用于指代消解）
        self.profile.last_intent = intent_result.intent
        if intent_result.slots:
            self.profile.last_slots = dict(intent_result.slots)

        # 收集订单号
        if order_id := intent_result.slots.get("order_id"):
            if order_id not in self.profile.mentioned_order_ids:
                self.profile.mentioned_order_ids.append(order_id)

        # 收集商品名
        if product_name := intent_result.slots.get("product_name"):
            if product_name not in self.profile.mentioned_products:
                self.profile.mentioned_products.append(product_name)

        # 记录投诉次数
        if intent_result.intent == "complaint":
            self.profile.complaint_count += 1

    def build_context_hint(self) -> str:
        """
        生成注入意图分类器的上下文提示。

        用途：帮助 LLM 做指代消解，例如：
          用户说 "就退那个" → 提示里有最近提到的订单号，LLM 能识别出来

        Returns:
            str: 格式化的上下文字符串，空时返回 ""
        """
        lines = []

        if self.profile.mentioned_order_ids:
            last_order = self.profile.mentioned_order_ids[-1]
            lines.append(f"本次会话中用户最近提到的订单号：{last_order}")

        if self.profile.mentioned_products:
            last_product = self.profile.mentioned_products[-1]
            lines.append(f"用户最近提到的商品：{last_product}")

        if self.profile.last_intent:
            lines.append(f"用户上一个意图：{self.profile.last_intent}")

        if not lines:
            return ""

        return "[会话上下文]\n" + "\n".join(lines)

    def get_last_order_id(self) -> Optional[str]:
        """返回本次会话最近提到的订单号，没有则返回 None"""
        return self.profile.mentioned_order_ids[-1] if self.profile.mentioned_order_ids else None

    def is_repeat_complainer(self, threshold: int = 2) -> bool:
        """判断用户是否多次投诉（用于路由决策）"""
        return self.profile.complaint_count >= threshold
