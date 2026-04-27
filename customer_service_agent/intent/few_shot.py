"""
Few-shot Examples 管理

为什么 Few-shot 比 Zero-shot 好得多？

Zero-shot: 告诉 LLM "你是意图识别器，识别以下意图..."
  → LLM 靠泛化能力，容易在边缘情况出错

Few-shot: 给 LLM 看具体例子
  → LLM 模仿例子的风格和边界，准确率大幅提升
  → 关键是例子要覆盖"难区分的边界情况"

工业级做法：
  - 静态 few-shot: 手工写的高质量样本（本文件）
  - 动态 few-shot: 根据当前输入，从例子库检索最相似的 K 条
    → 比静态好，因为例子和当前输入更相关
    → 需要向量检索（后续模块实现）
"""

from __future__ import annotations


# ─── 静态 Few-shot 样本库 ──────────────────────────────────────────────
# 选样原则：
#   1. 覆盖所有意图（每种至少 1 条）
#   2. 重点覆盖容易混淆的边界情况
#   3. 包含槽位完整和槽位缺失的例子

EXAMPLES: list[dict] = [
    # ── 清晰意图 ────────────────────────────────────────────
    {
        "input": "我的订单到哪了",
        "output": {
            "domain": "ORDER",
            "intent": "query_order_status",
            "confidence": 0.95,
            "slots": {},
            "secondary_intents": []
        },
        "note": "常见查询，order_id 缺失但不需要立刻追问（可以列出近期订单）"
    },
    {
        "input": "ORD-2024-001 这个订单我想取消",
        "output": {
            "domain": "ORDER",
            "intent": "cancel_order",
            "confidence": 0.97,
            "slots": {"order_id": "ORD-2024-001"},
            "secondary_intents": []
        },
        "note": "order_id 明确，直接提取"
    },

    # ── 模糊/低置信 ──────────────────────────────────────────
    {
        "input": "我想改一下",
        "output": {
            "domain": "ORDER",
            "intent": "modify_order",
            "confidence": 0.45,
            "slots": {},
            "secondary_intents": []
        },
        "note": "意图模糊，置信度要给低分，触发追问"
    },
    {
        "input": "有问题",
        "output": {
            "domain": "GENERAL",
            "intent": "unclear",
            "confidence": 0.30,
            "slots": {},
            "secondary_intents": []
        },
        "note": "完全模糊，unclear 意图"
    },

    # ── 多意图 ───────────────────────────────────────────────
    {
        "input": "上周买的手机壳能退吗？另外你们有蓝色的吗",
        "output": {
            "domain": "AFTER_SALES",
            "intent": "return_request",
            "confidence": 0.88,
            "slots": {"product_name": "手机壳"},
            "secondary_intents": [
                {
                    "domain": "PRODUCT",
                    "intent": "check_stock",
                    "confidence": 0.85,
                    "slots": {"product_name": "手机壳", "color": "蓝色"}
                }
            ]
        },
        "note": "多意图：主意图是退货，次意图是查库存"
    },

    # ── 容易混淆的边界 ────────────────────────────────────────
    {
        "input": "退款到账了吗",
        "output": {
            "domain": "AFTER_SALES",
            "intent": "refund_status",   # 注意：不是 return_request
            "confidence": 0.92,
            "slots": {},
            "secondary_intents": []
        },
        "note": "退款进度 ≠ 退货申请，是易混淆的边界"
    },
    {
        "input": "我要换货",
        "output": {
            "domain": "AFTER_SALES",
            "intent": "exchange_request",  # 换货 ≠ 退货
            "confidence": 0.90,
            "slots": {},
            "secondary_intents": []
        },
        "note": "换货和退货是不同意图，处理流程不一样"
    },
    {
        "input": "这个商品质量太差了，你们怎么卖这种东西",
        "output": {
            "domain": "AFTER_SALES",
            "intent": "complaint",
            "confidence": 0.85,
            "slots": {"issue_desc": "商品质量差"},
            "secondary_intents": []
        },
        "note": "投诉语气，不是退货申请，要路由到专门的投诉处理流程"
    },

    # ── 口语化表达 ────────────────────────────────────────────
    {
        "input": "能不能给我推荐个好一点的",
        "output": {
            "domain": "PRODUCT",
            "intent": "recommend",
            "confidence": 0.75,
            "slots": {},
            "secondary_intents": []
        },
        "note": "没有具体品类，槽位为空，但意图明确"
    },
    {
        "input": "你好",
        "output": {
            "domain": "GENERAL",
            "intent": "greeting",
            "confidence": 0.99,
            "slots": {},
            "secondary_intents": []
        },
        "note": "打招呼"
    },
]


def format_examples_for_prompt(examples: list[dict] | None = None) -> str:
    """
    将 few-shot 样本格式化为 prompt 可用的字符串。

    Args:
        examples: 如果传入 None，使用全量静态样本。
                  动态 few-shot 时传入检索到的最相关样本。
    """
    if examples is None:
        examples = EXAMPLES

    lines = ["以下是一些示例，帮助你理解判断标准：\n"]

    for i, ex in enumerate(examples, 1):
        import json
        lines.append(f"示例 {i}:")
        lines.append(f"  用户说: \"{ex['input']}\"")
        lines.append(f"  正确识别: {json.dumps(ex['output'], ensure_ascii=False)}")
        if ex.get("note"):
            lines.append(f"  说明: {ex['note']}")
        lines.append("")

    return "\n".join(lines)


# ─── 动态 Few-shot（简化版，后续会加向量检索）──────────────────────────

def select_relevant_examples(user_input: str, k: int = 4) -> list[dict]:
    """
    为当前输入选择最相关的 few-shot 样本。

    现在用关键词匹配（简单但有效）。
    后续升级为：向量相似度检索（语义匹配）。

    选择原则：
    1. 和当前输入语义相似的例子
    2. 覆盖当前输入可能涉及的边界情况
    """
    user_lower = user_input.lower()

    # 关键词 → 相关例子的粗略映射
    keyword_hints = {
        "退":     ["退款", "退货", "换货"],
        "换":     ["换货"],
        "取消":   ["取消订单"],
        "订单":   ["订单状态", "取消订单"],
        "查":     ["查询"],
        "推荐":   ["推荐"],
        "在吗":   ["打招呼"],
    }

    scored = []
    for ex in EXAMPLES:
        score = 0
        ex_input_lower = ex["input"].lower()

        # 简单关键词重叠分数
        for char in user_lower:
            if char in ex_input_lower and char not in " ，。？！":
                score += 1

        scored.append((score, ex))

    # 按分数排序，取 top-k，至少保留 1 条打招呼和 1 条模糊意图的例子
    scored.sort(key=lambda x: -x[0])
    selected = [ex for _, ex in scored[:k]]

    # 确保有一条置信度低的例子（帮 LLM 理解何时该给低分）
    has_low_conf = any(ex["output"]["confidence"] < 0.6 for ex in selected)
    if not has_low_conf:
        low_conf_example = next(
            (ex for ex in EXAMPLES if ex["output"]["confidence"] < 0.6), None
        )
        if low_conf_example and low_conf_example not in selected:
            selected[-1] = low_conf_example

    return selected
