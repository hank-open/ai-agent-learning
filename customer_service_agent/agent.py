"""
客服 Agent 主循环

完整流程：
  用户输入
    → 意图识别（classifier.py）
    → 路由决策（router.py）：AUTO / CONFIRM / HUMAN
    → 如果需要追问 → 返回追问
    → 根据意图选择工具并执行
    → 把工具结果 + 对话历史喂给 LLM
    → LLM 生成最终回复
    → 更新 SessionMemory

这个文件是整个系统的"大脑"，但它本身不做任何智能判断：
  - 意图判断 → classifier 负责
  - 路由决策 → router 负责
  - 数据查询 → tools 负责
  - 语言生成 → LLM 负责
  - Agent 只负责"编排"（orchestration）
"""

from __future__ import annotations

import time
import os
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

from .intent.classifier import classify
from .intent.few_shot import select_relevant_examples, format_examples_for_prompt
from .intent.schemas import Domain, OrderIntent, ProductIntent, AfterSalesIntent

from .tools.order_tools import lookup_order, cancel_order, get_user_recent_orders
from .tools.product_tools import search_products, check_stock, get_policy

from .memory import SessionMemory
from .routing import route, RoutingAction
from .monitoring import Tracer

client = Anthropic()


# ── 意图 → 工具 的映射表 ──────────────────────────────────────────────
#
# 每个工具函数签名：(slots: dict) -> str
# 用 lambda 包装统一接口，调用方只需 tool_fn(slots)

INTENT_TOOL_MAP: dict[str, callable] = {

    OrderIntent.QUERY_STATUS: lambda slots: (
        lookup_order(slots["order_id"])
        if slots.get("order_id")
        else get_user_recent_orders()
    ),

    OrderIntent.CANCEL: lambda slots: cancel_order(
        order_id=slots.get("order_id", ""),
        reason=slots.get("reason", ""),
    ),

    OrderIntent.MODIFY: lambda slots: (
        f"订单修改功能：{lookup_order(slots['order_id'])}\n\n"
        f"请告诉我您需要修改什么内容（地址/数量）？"
        if slots.get("order_id")
        else get_user_recent_orders()
    ),

    ProductIntent.SEARCH: lambda slots: search_products(
        query=slots.get("product_name", slots.get("category", ""))
    ),

    ProductIntent.CHECK_STOCK: lambda slots: check_stock(
        product_name=slots.get("product_name", ""),
        color=slots.get("color", ""),
    ),

    ProductIntent.RECOMMEND: lambda slots: search_products(
        query=slots.get("product_name")
              or slots.get("category")
              or slots.get("product_category")
              or "热门商品"
    ),

    AfterSalesIntent.RETURN: lambda slots: (
        get_policy("退货") + "\n\n" +
        (lookup_order(slots["order_id"]) if slots.get("order_id") else "")
    ),

    AfterSalesIntent.EXCHANGE: lambda slots: get_policy("换货"),

    AfterSalesIntent.REFUND_STATUS: lambda slots: (
        lookup_order(slots["order_id"])
        if slots.get("order_id")
        else get_user_recent_orders()
    ),

    AfterSalesIntent.COMPLAINT: lambda slots: (
        "已记录您的投诉，我们将在 24 小时内安排专员跟进。"
        f"问题描述：{slots.get('issue_desc', '未填写')}"
    ),
}


class CustomerServiceAgent:
    def __init__(self, verbose_trace: bool = False):
        self.history: list[dict] = []
        self.pending_intents: list = []

        # 新增：结构化会话记忆
        self.memory = SessionMemory()

        # 新增：调用链追踪（默认关闭详细输出，避免干扰正常对话）
        self.tracer = Tracer(verbose=verbose_trace)

    def chat(self, user_message: str) -> str:
        """处理一轮用户输入，返回 Agent 回复。"""

        self.tracer.start_turn()

        # ── Step 1: 意图识别 ──────────────────────────────────────────
        examples     = select_relevant_examples(user_message, k=3)
        few_shot_str = format_examples_for_prompt(examples)

        # 将 SessionMemory 的上下文提示注入 few-shot 之前，帮助指代消解
        context_hint = self.memory.build_context_hint()
        if context_hint:
            few_shot_str = context_hint + "\n\n" + few_shot_str

        t0 = time.perf_counter()
        intent_result = classify(
            user_message=user_message,
            conversation_history=self.history,
            few_shot_examples=few_shot_str,
        )
        intent_ms = (time.perf_counter() - t0) * 1000

        self.tracer.record_intent(intent_result.intent, intent_result.confidence, intent_ms)

        print(f"\n[意图] {intent_result.domain}/{intent_result.intent} "
              f"(置信:{intent_result.confidence:.2f}) "
              f"槽位:{intent_result.slots}")

        # ── Step 2: 路由决策 ─────────────────────────────────────────
        routing = route(
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            is_repeat_complainer=self.memory.is_repeat_complainer(),
        )

        print(f"[路由] {routing.action.value} — {routing.reason}")

        # 转人工：直接返回转接话术，跳过工具调用
        if routing.action == RoutingAction.HUMAN:
            reply = routing.human_handoff_message or "为您转接人工客服，请稍候。"
            self._add_to_history(user_message, reply)
            self.tracer.end_turn(user_message, reply, routing.action.value)
            return reply

        # ── Step 3: 追问判断 ─────────────────────────────────────────
        if intent_result.needs_clarification:
            reply = intent_result.clarification_question
            self._add_to_history(user_message, reply)
            self.tracer.end_turn(user_message, reply, "clarify")
            return reply

        # ── Step 4: 工具调用 ─────────────────────────────────────────
        tool_fn = INTENT_TOOL_MAP.get(intent_result.intent)

        if tool_fn:
            t0 = time.perf_counter()
            tool_result = tool_fn(intent_result.slots)
            tool_ms = (time.perf_counter() - t0) * 1000
            self.tracer.record_tool(intent_result.intent, tool_ms)
            print(f"[工具] {intent_result.intent} → {tool_result[:80]}...")
        else:
            tool_result = None

        # ── Step 5: 次级意图入队 ─────────────────────────────────────
        if intent_result.secondary_intents:
            self.pending_intents.extend(intent_result.secondary_intents)

        # ── Step 6: LLM 生成回复 ──────────────────────────────────────
        t0 = time.perf_counter()
        reply, usage = self._generate_reply(
            user_message=user_message,
            tool_result=tool_result,
            intent=intent_result.intent,
            routing_action=routing.action,
        )
        llm_ms = (time.perf_counter() - t0) * 1000
        self.tracer.record_llm(usage.get("input", 0), usage.get("output", 0), llm_ms)

        # ── Step 7: 更新记忆与历史 ────────────────────────────────────
        self.memory.update(intent_result, user_message)
        self._add_to_history(user_message, reply)

        # ── Step 8: 处理次级意图 ──────────────────────────────────────
        if self.pending_intents:
            next_intent = self.pending_intents.pop(0)
            next_tool_fn = INTENT_TOOL_MAP.get(next_intent.intent)
            if next_tool_fn:
                next_result = next_tool_fn(next_intent.slots)
                next_reply, _ = self._generate_reply(
                    user_message=f"[自动处理次级意图: {next_intent.intent}]",
                    tool_result=next_result,
                    intent=next_intent.intent,
                    routing_action=routing.action,
                )
                reply = reply + "\n\n另外，" + next_reply

        self.tracer.end_turn(user_message, reply, routing.action.value)
        return reply

    def _generate_reply(
        self,
        user_message: str,
        tool_result: str | None,
        intent: str,
        routing_action: RoutingAction = RoutingAction.AUTO,
    ) -> tuple[str, dict]:
        """
        调用 LLM 生成自然语言回复。

        Returns:
            (reply_text, usage_dict)  其中 usage_dict = {"input": N, "output": M}
        """
        # CONFIRM 模式在 system prompt 里加一句"请提示用户核实"
        confirm_note = (
            "\n如果涉及订单操作（取消/退货/换货），请在回复末尾加一句：\n"
            "「如有任何疑问，请回复确认或告诉我您的需求」"
            if routing_action == RoutingAction.CONFIRM else ""
        )

        system = (
            "你是一位专业、友善的电商平台客服。\n"
            "根据下面的工具查询结果，用自然、简洁的语言回复用户。\n"
            "不要重复工具结果的所有字段，只说用户关心的关键信息。\n"
            "语气友善，如有需要可以主动询问是否还有其他问题。"
            + confirm_note
        )

        messages = list(self.history)

        if tool_result:
            content = f"{user_message}\n\n[工具查询结果]:\n{tool_result}"
        else:
            content = user_message

        messages.append({"role": "user", "content": content})

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system,
            messages=messages,
        )

        usage = {
            "input":  response.usage.input_tokens,
            "output": response.usage.output_tokens,
        }
        return response.content[0].text, usage

    def _add_to_history(self, user_message: str, assistant_reply: str):
        self.history.append({"role": "user",      "content": user_message})
        self.history.append({"role": "assistant",  "content": assistant_reply})

        # 只保留最近 20 条（10 轮），避免 token 无限增长
        if len(self.history) > 20:
            self.history = self.history[-20:]
