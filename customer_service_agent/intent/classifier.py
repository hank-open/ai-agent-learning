"""
意图分类器

工程决策：为什么用 structured output 而不是 prompt 文本解析？

方案 A（脆弱）:
  让 LLM 输出 "意图: ORDER/cancel_order, 槽位: order_id=xxx"
  → 然后用正则解析
  → 问题: LLM 输出格式不稳定，正则一变就全坏

方案 B（本文件使用）:
  让 LLM 直接输出 JSON，用 Pydantic 验证
  → Claude 的 tool_use 机制强制输出结构化 JSON
  → 解析失败可以自动重试（有 schema 可以提示 LLM 修正）

方案 C（工业级）:
  在 B 的基础上加 few-shot examples 提升准确率
  → 见 few_shot.py
"""

from __future__ import annotations

import json
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from .schemas import (
    IntentResult, Domain, OrderIntent, ProductIntent,
    AfterSalesIntent, AccountIntent, GeneralIntent,
    get_missing_required_slots,
)

client = Anthropic()

# ─── 工具定义（用 tool_use 强制结构化输出）────────────────────────────

INTENT_TOOL = {
    "name": "classify_intent",
    "description": "对用户消息进行意图识别和槽位提取",
    "input_schema": {
        "type": "object",
        "properties": {
            "domain": {
                "type": "string",
                "enum": [d.value for d in Domain],
                "description": "粗粒度域"
            },
            "intent": {
                "type": "string",
                "enum": (
                    [i.value for i in OrderIntent] +
                    [i.value for i in ProductIntent] +
                    [i.value for i in AfterSalesIntent] +
                    [i.value for i in AccountIntent] +
                    [i.value for i in GeneralIntent]
                ),
                "description": "细粒度意图"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "识别置信度"
            },
            "slots": {
                "type": "object",
                "description": "提取的槽位，如 {order_id: 'ORD-001', reason: '不想要了'}",
                "additionalProperties": {"type": "string"}
            },
            "secondary_intents": {
                "type": "array",
                "description": "用户同时表达了多个意图时，填写次级意图",
                "items": {
                    "type": "object",
                    "properties": {
                        "domain":   {"type": "string"},
                        "intent":   {"type": "string"},
                        "confidence": {"type": "number"},
                        "slots":    {"type": "object"}
                    },
                    "required": ["domain", "intent", "confidence", "slots"]
                }
            }
        },
        "required": ["domain", "intent", "confidence", "slots", "secondary_intents"]
    }
}

# ─── System Prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个电商平台客服系统的意图识别模块。

你的任务是分析用户消息，识别：
1. 粗粒度域（ORDER/PRODUCT/AFTER_SALES/ACCOUNT/GENERAL）
2. 细粒度意图（具体操作）
3. 槽位信息（关键参数，如订单号、商品名等）
4. 置信度（你有多确定这个判断）

注意事项：
- 如果用户一句话包含多个意图，把主要的放在主意图，其余放在 secondary_intents
- 置信度诚实评估：如果用户表达模糊就给低分，不要强行高置信
- 槽位只提取明确提到的信息，不要推断没有的
- 用户可能用口语，如"上周买的那个"="recent_purchase"

{few_shot_examples}
"""


# ─── 核心分类函数 ─────────────────────────────────────────────────────

def classify(
    user_message: str,
    conversation_history: list[dict] | None = None,
    few_shot_examples: str = "",
) -> IntentResult:
    """
    对单条用户消息进行意图识别。

    Args:
        user_message:          当前用户消息
        conversation_history:  历史对话（用于消解指代，如"就是刚才说的那个"）
        few_shot_examples:     动态注入的 few-shot 示例（见 few_shot.py）

    Returns:
        IntentResult（Pydantic 验证过的结构）
    """
    system = SYSTEM_PROMPT.format(few_shot_examples=few_shot_examples)

    # 构建消息列表
    # 历史对话有助于解决指代消解：
    # "就退那个" → 需要上文知道"那个"是什么
    messages = []
    if conversation_history:
        # 只取最近 6 轮，避免 token 过多
        messages.extend(conversation_history[-12:])

    messages.append({"role": "user", "content": user_message})

    # 调用 Claude，强制使用 tool_use 输出结构化结果
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=system,
        tools=[INTENT_TOOL],
        tool_choice={"type": "auto"},
        messages=messages,
    )

    # 解析 tool_use 输出
    raw = _extract_tool_call(response)

    # 构建 IntentResult（Pydantic 会做类型校验）
    result = IntentResult(
        domain=raw["domain"],
        intent=raw["intent"],
        confidence=raw["confidence"],
        slots=raw.get("slots", {}),
        secondary_intents=[
            IntentResult(
                domain=s["domain"],
                intent=s["intent"],
                confidence=s["confidence"],
                slots=s.get("slots", {}),
            )
            for s in raw.get("secondary_intents", [])
        ],
    )

    # 追问决策：必填槽位缺失 → 标记需要追问
    missing = get_missing_required_slots(result.intent, result.slots)
    if missing or result.confidence < 0.5:
        result.needs_clarification = True
        result.clarification_question = _build_clarification_question(
            result.intent, missing, result.confidence
        )

    return result


def _extract_tool_call(response) -> dict:
    """从 Claude 响应中提取 tool_use 内容"""
    for block in response.content:
        if block.type == "tool_use" and block.name == "classify_intent":
            return block.input
    # Fallback：如果 LLM 没有调用工具（不应该发生，但要防御）
    raise ValueError(
        f"LLM 未调用 classify_intent 工具，原始响应: {response.content}"
    )


def _build_clarification_question(intent: str, missing_slots: list[str], confidence: float) -> str:
    """根据缺失槽位或低置信度，生成追问话术"""

    if confidence < 0.5:
        return "您好，我没有完全理解您的问题，能麻烦您说得更具体一些吗？"

    slot_questions = {
        "order_id":  "请问您的订单号是多少？（通常是 ORD- 开头）",
        "reason":    "请问您取消/退换的原因是什么？",
        "new_address": "请问您需要修改成什么地址？",
    }

    if missing_slots:
        # 一次只追问一个槽位（避免用户被多个问题淹没）
        first_missing = missing_slots[0]
        return slot_questions.get(first_missing, f"请问您能提供更多关于 {first_missing} 的信息吗？")

    return "请问您能说得更具体一些吗？"
