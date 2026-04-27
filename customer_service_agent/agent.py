"""
客服 Agent 主循环

完整流程：
  用户输入
    → 意图识别（classifier.py）
    → 如果需要追问 → 返回追问
    → 根据意图选择工具并执行
    → 把工具结果 + 对话历史喂给 LLM
    → LLM 生成最终回复

这个文件是整个系统的"大脑"，但它本身不做任何智能判断：
  - 意图判断 → classifier 负责
  - 数据查询 → tools 负责
  - 语言生成 → LLM 负责
  Agent 只负责"编排"（orchestration）
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()                          # 从 .env 文件加载 ANTHROPIC_API_KEY

from anthropic import Anthropic

# 意图识别模块
from .intent.classifier import classify
from .intent.few_shot import select_relevant_examples, format_examples_for_prompt
from .intent.schemas import Domain, OrderIntent, ProductIntent, AfterSalesIntent

# 工具模块
from .tools.order_tools import lookup_order, cancel_order, get_user_recent_orders
from .tools.product_tools import search_products, check_stock, get_policy

# Anthropic 客户端（全局单例，避免重复创建）
client = Anthropic()


# ── 意图 → 工具 的映射表 ──────────────────────────────────────────────
#
# 设计思路：把"什么意图用什么工具"集中在一个地方管理，
# 而不是散落在 if-elif 链里。这样增加新意图时只需加一行。
#
# 每个工具函数签名：(slots: dict) -> str
# 用 lambda 包装是为了统一接口：工具函数的参数各不相同，
# 但调用方只需要 tool_fn(slots) 就够了。

INTENT_TOOL_MAP: dict[str, callable] = {

    # ── 订单意图 ─────────────────────────────────────────────────────
    OrderIntent.QUERY_STATUS: lambda slots: (
        lookup_order(slots["order_id"])
        if slots.get("order_id")
        # order_id 缺失时，展示近期订单列表（而不是报错）
        else get_user_recent_orders()
    ),

    OrderIntent.CANCEL: lambda slots: cancel_order(
        order_id=slots.get("order_id", ""),
        reason=slots.get("reason", ""),
    ),

    OrderIntent.MODIFY: lambda slots: (
        # 修改订单目前只支持查状态（完整实现需要更多工具，先占位）
        f"订单修改功能：{lookup_order(slots['order_id'])}\n\n"
        f"请告诉我您需要修改什么内容（地址/数量）？"
        if slots.get("order_id")
        else get_user_recent_orders()
    ),

    # ── 商品意图 ─────────────────────────────────────────────────────
    ProductIntent.SEARCH: lambda slots: search_products(
        query=slots.get("product_name", slots.get("category", ""))
    ),

    ProductIntent.CHECK_STOCK: lambda slots: check_stock(
        product_name=slots.get("product_name", ""),
        color=slots.get("color", ""),
    ),

    ProductIntent.RECOMMEND: lambda slots: search_products(
        # LLM 提取的 key 可能是 product_name / category / product_category，都兼容
        query=slots.get("product_name")
              or slots.get("category")
              or slots.get("product_category")
              or "热门商品"
    ),

    # ── 售后意图 ─────────────────────────────────────────────────────
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


# ── 对话历史管理 ──────────────────────────────────────────────────────
#
# 多轮对话的核心：把每一轮的 user/assistant 消息存起来，
# 每次调用 LLM 时都传入完整历史，LLM 才能"记住"之前说了什么。
#
# 注意：这是 Session-level 的内存（仅当前会话有效）。
# 模块 3（Memory）会讲如何做跨会话的持久化记忆。

class CustomerServiceAgent:
    def __init__(self):
        # 对话历史：[{"role": "user"/"assistant", "content": "..."}]
        # 这个列表会随着对话增长
        self.history: list[dict] = []

        # 待处理的次级意图队列
        # 多意图场景：主意图先处理，次意图存这里，下一轮触发
        self.pending_intents: list = []

    def chat(self, user_message: str) -> str:
        """
        处理一轮用户输入，返回 Agent 回复。

        这是对外的唯一接口，外部调用者不需要知道内部逻辑。
        """

        # ── Step 1: 意图识别 ─────────────────────────────────────────
        #
        # 动态 few-shot：根据用户当前输入，选最相关的示例
        # 比静态 few-shot 准确率高，因为示例和当前情况更相似
        examples = select_relevant_examples(user_message, k=3)
        few_shot_str = format_examples_for_prompt(examples)

        # 传入对话历史，用于指代消解（"就退那个" → 知道"那个"是什么）
        intent_result = classify(
            user_message=user_message,
            conversation_history=self.history,
            few_shot_examples=few_shot_str,
        )

        print(f"\n[意图] {intent_result.domain}/{intent_result.intent} "
              f"(置信:{intent_result.confidence:.2f}) "
              f"槽位:{intent_result.slots}")

        # ── Step 2: 追问判断 ─────────────────────────────────────────
        #
        # 如果意图识别发现需要追问（缺必填槽位或置信度低），
        # 直接返回追问，不调用工具
        if intent_result.needs_clarification:
            reply = intent_result.clarification_question

            # 把这一轮存入历史（追问也是对话的一部分）
            self._add_to_history(user_message, reply)
            return reply

        # ── Step 3: 工具调用 ─────────────────────────────────────────
        #
        # 根据意图查找对应工具并执行
        tool_fn = INTENT_TOOL_MAP.get(intent_result.intent)

        if tool_fn:
            # 执行工具，获取数据
            tool_result = tool_fn(intent_result.slots)
            print(f"[工具] {intent_result.intent} → {tool_result[:80]}...")
        else:
            # 没有对应工具（GENERAL 域的打招呼等），直接让 LLM 回答
            tool_result = None

        # ── Step 4: 把次级意图加入待处理队列 ────────────────────────
        #
        # 如"退手机壳，另外有没有蓝色的"
        # 主意图 return_request 处理完后，把 check_stock 存入队列
        if intent_result.secondary_intents:
            self.pending_intents.extend(intent_result.secondary_intents)

        # ── Step 5: 让 LLM 生成最终回复 ─────────────────────────────
        #
        # 把"工具查到的数据"作为上下文，让 LLM 用自然语言表达
        # 而不是直接把工具结果返回给用户（那样太生硬）
        reply = self._generate_reply(
            user_message=user_message,
            tool_result=tool_result,
            intent=intent_result.intent,
        )

        # ── Step 6: 更新对话历史 ─────────────────────────────────────
        self._add_to_history(user_message, reply)

        # ── Step 7: 处理次级意图（如果有）──────────────────────────
        #
        # 如果还有次级意图待处理，追加一句提示
        if self.pending_intents:
            next_intent = self.pending_intents.pop(0)
            next_tool_fn = INTENT_TOOL_MAP.get(next_intent.intent)
            if next_tool_fn:
                next_result = next_tool_fn(next_intent.slots)
                # 把次级意图的结果也用 LLM 生成回复，追加在后面
                next_reply = self._generate_reply(
                    user_message=f"[自动处理次级意图: {next_intent.intent}]",
                    tool_result=next_result,
                    intent=next_intent.intent,
                )
                reply = reply + "\n\n另外，" + next_reply

        return reply

    def _generate_reply(
        self,
        user_message: str,
        tool_result: str | None,
        intent: str,
    ) -> str:
        """
        调用 LLM 生成自然语言回复。

        为什么不直接返回工具结果？
          工具结果是数据，LLM 把它转成自然语言回复。
          例如工具返回"订单状态: shipped"，
          LLM 会说"您的订单已发货，预计明天到达，请注意查收"。
          这样的回复更自然、更有温度。
        """

        # 构建给 LLM 的 system prompt
        system = (
            "你是一位专业、友善的电商平台客服。\n"
            "根据下面的工具查询结果，用自然、简洁的语言回复用户。\n"
            "不要重复工具结果的所有字段，只说用户关心的关键信息。\n"
            "语气友善，如有需要可以主动询问是否还有其他问题。"
        )

        # 构建消息列表：历史对话 + 当前轮次
        messages = list(self.history)  # 复制一份，不改原列表

        # 如果有工具结果，把它作为额外上下文注入当前用户消息
        # 格式：用户原始问题 + 工具查到的数据
        if tool_result:
            content = (
                f"{user_message}\n\n"
                f"[工具查询结果]:\n{tool_result}"
            )
        else:
            content = user_message

        messages.append({"role": "user", "content": content})

        # 调用 LLM
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system,
            messages=messages,
        )

        return response.content[0].text

    def _add_to_history(self, user_message: str, assistant_reply: str):
        """
        把这一轮对话加入历史。

        注意：存的是原始用户消息，不存工具结果。
        原因：历史是给意图识别用的（做指代消解），
              它只需要知道用户说了什么，不需要工具结果。
        """
        self.history.append({"role": "user",      "content": user_message})
        self.history.append({"role": "assistant",  "content": assistant_reply})

        # 限制历史长度：只保留最近 20 条（10 轮对话）
        # 避免 token 无限增长 → 成本高 + 性能慢
        # 真实系统里超出时做摘要压缩（模块 3 会讲）
        if len(self.history) > 20:
            # 保留最新的 20 条
            self.history = self.history[-20:]
