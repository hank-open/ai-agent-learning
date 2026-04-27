"""
运行客服 Agent

两种模式：
  1. 自动测试：跑预设对话场景，验证系统
  2. 交互模式：真人输入，实时对话

运行方式：
  python -m customer_service_agent.run
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from customer_service_agent.agent import CustomerServiceAgent


def run_scenario(agent: CustomerServiceAgent, scenario_name: str, turns: list[str]):
    """运行一个预设对话场景"""
    print(f"\n{'='*65}")
    print(f"场景：{scenario_name}")
    print(f"{'='*65}")

    # 每个场景用全新的 agent，对话历史互不干扰
    agent.history.clear()
    agent.pending_intents.clear()

    for user_msg in turns:
        print(f"\n用户：{user_msg}")
        reply = agent.chat(user_msg)
        print(f"客服：{reply}")


def run_auto_tests():
    """自动跑预设场景，覆盖所有主要分支"""

    agent = CustomerServiceAgent()

    scenarios = [
        # ── 场景 1：清晰查单 ─────────────────────────────────────
        (
            "清晰查单（带订单号）",
            ["我的订单 ORD-2024-001 到哪了"]
        ),

        # ── 场景 2：缺订单号 → 追问 → 补充后处理 ───────────────
        (
            "取消订单（缺订单号）",
            [
                "我要取消订单",           # 缺 order_id → 触发追问
                "是 ORD-2024-003",        # 补充后，agent 要处理取消
            ]
        ),

        # ── 场景 3：多轮查单 + 指代 ──────────────────────────────
        (
            "指代消解：「这个」指上文的订单",
            [
                "帮我查一下 ORD-2024-002",
                "这个能退吗",             # 「这个」= ORD-2024-002
            ]
        ),

        # ── 场景 4：多意图 ─────────────────────────────────────
        (
            "多意图：退货 + 查库存",
            ["上周买的手机壳能退吗？另外你们有蓝色的手机壳吗"]
        ),

        # ── 场景 5：商品搜索 ──────────────────────────────────
        (
            "商品搜索",
            ["我想买一个降噪耳机，有什么推荐吗"]
        ),

        # ── 场景 6：查库存 ─────────────────────────────────────
        (
            "查特定颜色库存",
            ["蓝牙耳机 Pro 有蓝色的吗"]
        ),

        # ── 场景 7：投诉 ──────────────────────────────────────
        (
            "投诉处理",
            ["这个商品质量太差了，买来就坏了，你们怎么卖这种东西"]
        ),
    ]

    for name, turns in scenarios:
        run_scenario(agent, name, turns)


def run_interactive():
    """交互模式：真人输入"""
    agent = CustomerServiceAgent()

    print("\n客服 Agent 已启动（输入 quit 退出，输入 clear 清空对话历史）\n")
    print("可以试试这些问题：")
    print("  • 我的订单 ORD-2024-001 到哪了")
    print("  • 我要取消订单")
    print("  • 手机壳有蓝色的吗")
    print("  • 上周买的耳机能退吗")
    print()

    while True:
        try:
            user_input = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("再见！")
            break

        if user_input.lower() == "clear":
            agent.history.clear()
            agent.pending_intents.clear()
            print("[对话历史已清空]\n")
            continue

        reply = agent.chat(user_input)
        print(f"客服：{reply}\n")


if __name__ == "__main__":
    # 先跑自动测试，再进入交互模式
    print("── 自动场景测试 ──")
    run_auto_tests()

    print(f"\n\n{'='*65}")
    print("── 进入交互模式 ──")
    run_interactive()
