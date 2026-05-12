"""
路由决策模块

核心职责：根据意图置信度 + 业务规则，决定请求走哪条路径。

三条路径：
  AUTO     → 置信度高 (≥0.8)，直接自动处理
  CONFIRM  → 置信度中 (0.5–0.8)，自动处理但提示用户确认
  HUMAN    → 置信度低 (<0.5) 或 高风险操作 或 多次投诉，转人工

工程价值：
  把路由规则集中在一处，而不是散落在各个 if-elif 里。
  增加新规则只改这个文件，主流程不动。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RoutingAction(str, Enum):
    AUTO    = "auto"     # 自动处理，无需确认
    CONFIRM = "confirm"  # 自动处理，但附加"如有问题请告知"
    HUMAN   = "human"    # 转人工客服


@dataclass
class RoutingDecision:
    action: RoutingAction
    reason: str                      # 给开发者看的诊断信息
    human_handoff_message: Optional[str] = None  # 转人工时的提示话术


# ── 高风险意图：即使置信度高，也要走 CONFIRM ──────────────────────────
# 原因：取消/退货这类不可逆操作出错代价大，多一次确认值得
HIGH_RISK_INTENTS = {
    "cancel_order",
    "return_request",
    "exchange_request",
}


def route(
    intent: str,
    confidence: float,
    is_repeat_complainer: bool = False,
) -> RoutingDecision:
    """
    根据意图和置信度返回路由决策。

    Args:
        intent:               细粒度意图字符串
        confidence:           意图识别置信度 0-1
        is_repeat_complainer: 是否多次投诉（来自 SessionMemory）

    Returns:
        RoutingDecision
    """
    # ── 规则 1：多次投诉 → 直接转人工（优先级最高）────────────────
    if is_repeat_complainer and intent == "complaint":
        return RoutingDecision(
            action=RoutingAction.HUMAN,
            reason="用户多次投诉，需要人工专员介入",
            human_handoff_message=(
                "您好，我注意到您已多次反馈问题，非常抱歉给您带来不便。"
                "我已为您升级处理，专属客服将在 5 分钟内联系您。"
            ),
        )

    # ── 规则 2：低置信 → 转人工或追问 ────────────────────────────
    if confidence < 0.5:
        return RoutingDecision(
            action=RoutingAction.HUMAN,
            reason=f"置信度过低 ({confidence:.2f})，无法自动处理",
            human_handoff_message=(
                "您的问题比较复杂，我为您转接人工客服，稍候为您服务。"
            ),
        )

    # ── 规则 3：高风险意图 → CONFIRM（不转人工，但降级为确认模式）──
    if intent in HIGH_RISK_INTENTS:
        return RoutingDecision(
            action=RoutingAction.CONFIRM,
            reason=f"高风险意图 {intent}，附加确认提示",
        )

    # ── 规则 4：中置信 → CONFIRM ──────────────────────────────────
    if confidence < 0.8:
        return RoutingDecision(
            action=RoutingAction.CONFIRM,
            reason=f"置信度偏低 ({confidence:.2f})，附加确认提示",
        )

    # ── 默认：高置信 + 非高风险 → AUTO ───────────────────────────
    return RoutingDecision(
        action=RoutingAction.AUTO,
        reason=f"置信度 {confidence:.2f}，自动处理",
    )
