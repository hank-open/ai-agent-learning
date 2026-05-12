"""
意图识别评测套件

评测的核心价值：
  - 没有评测就没有改进的基准
  - 每次改动 prompt / few-shot，都能量化看到效果
  - 可以发现哪些意图容易混淆（precision 低的地方）

指标：
  - 准确率（Accuracy）：整体识别正确率
  - 精确率（Precision）：预测为意图 X 的样本中，真的是 X 的比例
  - 召回率（Recall）：真正是意图 X 的样本中，被正确识别的比例
  - F1：精确率和召回率的调和平均

运行：
  python -m customer_service_agent.evaluation.intent_eval
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Optional

from customer_service_agent.intent.classifier import classify


# ── 评测数据集 ────────────────────────────────────────────────────────
#
# 原则：
#   1. 覆盖所有意图（每种 ≥ 2 条）
#   2. 重点覆盖容易混淆的边界（退款状态 vs 退货申请 vs 换货）
#   3. 包含口语、错别字、缩写等真实用户表达
#
# 扩展方法：把真实用户对话脱敏后加进来，准确率会更高

EVAL_DATASET: list[dict] = [
    # ── ORDER ────────────────────────────────────────────────
    {"input": "我的订单 ORD-2024-001 现在在哪", "expected_intent": "query_order_status"},
    {"input": "帮我查一下订单状态",              "expected_intent": "query_order_status"},
    {"input": "ORD-2024-003 我想取消",           "expected_intent": "cancel_order"},
    {"input": "帮我取消订单，我不想要了",         "expected_intent": "cancel_order"},
    {"input": "我要修改收货地址",                 "expected_intent": "modify_order"},
    {"input": "能改一下快递地址吗",               "expected_intent": "modify_order"},

    # ── PRODUCT ──────────────────────────────────────────────
    {"input": "你们有降噪耳机吗",                 "expected_intent": "product_search"},
    {"input": "帮我找一个机械键盘",               "expected_intent": "product_search"},
    {"input": "蓝牙耳机 Pro 还有蓝色的吗",        "expected_intent": "check_stock"},
    {"input": "手机壳有没有红色",                 "expected_intent": "check_stock"},
    {"input": "给我推荐个好用的键盘",             "expected_intent": "recommend"},
    {"input": "有什么耳机值得买",                 "expected_intent": "recommend"},

    # ── AFTER_SALES ─── 容易混淆的区域 ───────────────────────
    {"input": "我要退货",                         "expected_intent": "return_request"},
    {"input": "上周买的耳机能退吗",               "expected_intent": "return_request"},
    {"input": "我要换一个，这个坏了",             "expected_intent": "exchange_request"},
    {"input": "换货怎么申请",                     "expected_intent": "exchange_request"},
    {"input": "退款到账了吗",                     "expected_intent": "refund_status"},   # 退款进度 ≠ 退货
    {"input": "我的退款什么时候能到",             "expected_intent": "refund_status"},
    {"input": "这个商品质量太差了",               "expected_intent": "complaint"},
    {"input": "你们客服态度太差，要投诉",         "expected_intent": "complaint"},

    # ── GENERAL ──────────────────────────────────────────────
    {"input": "你好",                             "expected_intent": "greeting"},
    {"input": "在吗",                             "expected_intent": "greeting"},
    {"input": "拜拜",                             "expected_intent": "farewell"},
    {"input": "谢谢，再见",                       "expected_intent": "farewell"},
    # {"input": "上周买的耳机能退吗，你们怎么处理我的换货问题",         "expected_intent": "exchange_request"},
]


@dataclass
class EvalResult:
    total:          int
    correct:        int
    accuracy:       float
    per_intent:     dict = field(default_factory=dict)   # intent → {tp, fp, fn, precision, recall, f1}
    errors:         list = field(default_factory=list)   # 识别错误的样本，用于诊断


def evaluate_intent_classifier(
    dataset: list[dict] | None = None,
    verbose: bool = True,
) -> EvalResult:
    """
    跑完整评测，返回 EvalResult。

    Args:
        dataset: 评测样本列表，None 时使用内置 EVAL_DATASET
        verbose: 是否打印每条样本的结果

    Returns:
        EvalResult with accuracy, per-intent precision/recall/F1
    """
    if dataset is None:
        dataset = EVAL_DATASET

    # tp[intent] = true positive count
    tp: dict[str, int] = defaultdict(int)
    fp: dict[str, int] = defaultdict(int)
    fn: dict[str, int] = defaultdict(int)

    correct = 0
    errors  = []

    print(f"\n开始评测，共 {len(dataset)} 条样本...\n")

    for i, sample in enumerate(dataset, 1):
        user_input     = sample["input"]
        expected       = sample["expected_intent"]

        try:
            result   = classify(user_input)
            predicted = result.intent
        except Exception as e:
            predicted = f"ERROR:{e}"

        is_correct = (predicted == expected)

        if is_correct:
            correct += 1
            tp[expected] += 1
        else:
            fp[predicted] += 1
            fn[expected]  += 1
            errors.append({
                "input":     user_input,
                "expected":  expected,
                "predicted": predicted,
                "confidence": getattr(result, "confidence", 0.0) if "result" in dir() else 0.0,
            })

        if verbose:
            mark = "✓" if is_correct else "✗"
            print(f"  [{mark}] {user_input[:30]:<30} expected={expected:<25} got={predicted}")

    # ── 计算 per-intent 指标 ──────────────────────────────────────────
    all_intents = set(tp.keys()) | set(fp.keys()) | set(fn.keys())
    per_intent  = {}

    for intent in sorted(all_intents):
        t  = tp[intent]
        f_p = fp[intent]
        f_n = fn[intent]
        precision = t / (t + f_p) if (t + f_p) > 0 else 0.0
        recall    = t / (t + f_n) if (t + f_n) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)
        per_intent[intent] = {
            "tp": t, "fp": f_p, "fn": f_n,
            "precision": round(precision, 3),
            "recall":    round(recall, 3),
            "f1":        round(f1, 3),
        }

    accuracy = correct / len(dataset) if dataset else 0.0
    result   = EvalResult(
        total=len(dataset),
        correct=correct,
        accuracy=round(accuracy, 3),
        per_intent=per_intent,
        errors=errors,
    )

    _print_report(result)
    return result


def _print_report(result: EvalResult) -> None:
    print(f"\n{'='*60}")
    print(f"评测结果：{result.correct}/{result.total}  准确率 {result.accuracy:.1%}")
    print(f"{'='*60}")
    print(f"\n{'意图':<30} {'P':>6} {'R':>6} {'F1':>6}")
    print(f"{'-'*50}")
    for intent, m in result.per_intent.items():
        print(f"  {intent:<28} {m['precision']:>6.3f} {m['recall']:>6.3f} {m['f1']:>6.3f}")

    if result.errors:
        print(f"\n错误样本（共 {len(result.errors)} 条）：")
        for e in result.errors:
            print(f"  输入: {e['input']}")
            print(f"    期望: {e['expected']}  预测: {e['predicted']}  置信: {e.get('confidence', '?'):.2f}")


if __name__ == "__main__":
    evaluate_intent_classifier()
