"""
意图识别测试脚本

运行: python -m customer_service_agent.intent.test_intent
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv()

from customer_service_agent.intent.classifier import classify
from customer_service_agent.intent.few_shot import select_relevant_examples, format_examples_for_prompt


def print_result(msg: str, result):
    """打印意图识别结果"""
    print(f"\n{'─'*60}")
    print(f"用户: {msg}")
    print(f"域:   {result.domain}  意图: {result.intent}  置信: {result.confidence:.2f}")

    if result.slots:
        print(f"槽位: {result.slots}")

    if result.secondary_intents:
        for si in result.secondary_intents:
            print(f"次要意图: {si.domain}/{si.intent} ({si.confidence:.2f}) 槽位: {si.slots}")

    if result.needs_clarification:
        print(f"⚠ 需要追问: {result.clarification_question}")
    else:
        print(f"✅ 可以直接处理")


def run_tests():
    test_cases = [
        # (测试描述, 用户消息, 是否带对话历史)
        ("清晰查单",        "我的订单 ORD-2024-001 到哪了",               False),
        ("槽位缺失-取消",   "我要取消订单",                               False),
        ("模糊意图",        "我想改一下",                                  False),
        ("多意图",          "上周买的手机壳能退吗？另外你们有蓝色的吗",    False),
        ("投诉 vs 退货",    "这个商品质量太差了，你们怎么卖这种东西",      False),
        ("退款 vs 退货",    "我申请退款了，钱到账了吗",                    False),
        ("口语化",          "能不能给我推荐个便宜点的耳机",               False),

        # 指代消解：需要上文才能理解
        ("指代消解",        "就退那个",
         [  # 对话历史
             {"role": "user",      "content": "我上周买的蓝牙耳机有点问题"},
             {"role": "assistant", "content": "您好，请问是什么问题？"},
         ]),
    ]

    for desc, msg, history in test_cases:
        print(f"\n\n{'='*60}")
        print(f"测试: {desc}")

        # 选择动态 few-shot 示例
        examples = select_relevant_examples(msg, k=3)
        few_shot_str = format_examples_for_prompt(examples)

        result = classify(
            user_message=msg,
            conversation_history=history if history else None,
            few_shot_examples=few_shot_str,
        )
        print_result(msg, result)


if __name__ == "__main__":
    run_tests()
