"""
使用 LangChain 1.x 的 Agent（现代 LCEL 写法）
对比手写版本，看框架如何简化开发

学习重点:
- @tool 装饰器
- bind_tools() 让 LLM 直接输出工具调用（JSON，不是文本解析）
- LCEL 管道：prompt | llm.bind_tools(tools)
- 手动驱动工具调用循环（清晰可见）
"""

from dotenv import load_dotenv
load_dotenv()

import json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_anthropic import ChatAnthropic


# ─── 工具定义（@tool 装饰器，比手写字典更优雅）────────────────────

@tool
def calculator(expression: str) -> str:
    """计算数学表达式，如 '2 + 2 * 3' 或 '12742 - 6779'"""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "错误: 表达式包含非法字符"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def web_search(query: str) -> str:
    """搜索天文、地理等知识"""
    knowledge_base = {
        "火星直径": "火星的直径约为 6,779 公里",
        "火星":     "火星是太阳系的第四颗行星，平均温度约 -80°C",
        "地球直径": "地球的直径约为 12,742 公里",
        "地球":     "地球是太阳系的第三颗行星，表面积约 5.1 亿平方公里",
        "月球直径": "月球的直径约为 3,474 公里",
        "月球":     "月球是地球的卫星，距地球约 384,400 公里",
    }
    for key, value in knowledge_base.items():
        if key.lower() in query.lower():
            return value
    return f"未找到关于 '{query}' 的信息"


@tool
def code_executor(code: str) -> str:
    """执行简单的 Python 数学表达式，如 '15 ** 2' 或 '3.14 * 5 ** 2'"""
    forbidden = ["import", "open", "exec", "eval", "__", "os", "sys"]
    for kw in forbidden:
        if kw in code.lower():
            return f"错误: 禁止操作 '{kw}'"
    try:
        return str(eval(code))
    except Exception as e:
        return f"执行错误: {str(e)}"


# ─── Agent 构建（LCEL 现代写法）────────────────────────────────────

TOOLS = [calculator, web_search, code_executor]
TOOL_MAP = {t.name: t for t in TOOLS}


def run_langchain_agent(question: str, max_iterations: int = 10) -> str:
    """
    用 LangChain 1.x LCEL 风格运行 Agent。

    核心思路：
    1. llm.bind_tools(tools)  → LLM 知道有哪些工具
    2. LLM 返回 AIMessage，其中包含 tool_calls（JSON 格式，不用文本解析！）
    3. 执行工具，把结果包装成 ToolMessage 传回
    4. 循环，直到 LLM 不再调用工具
    """
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=1000)
    llm_with_tools = llm.bind_tools(TOOLS)

    messages = [HumanMessage(content=question)]

    print(f"\n{'='*60}")
    print(f"问题: {question}")
    print(f"{'='*60}")

    for iteration in range(max_iterations):
        print(f"\n--- 迭代 {iteration + 1} ---")

        response: AIMessage = llm_with_tools.invoke(messages)
        messages.append(response)

        # 没有工具调用 → 最终答案
        if not response.tool_calls:
            print(f"LLM 回答: {response.content}")
            return response.content

        # 有工具调用 → 执行每个工具
        for tc in response.tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id   = tc["id"]

            print(f"  工具调用: {tool_name}({tool_args})")

            tool_result = TOOL_MAP[tool_name].invoke(tool_args)
            print(f"  工具结果: {tool_result}")

            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_id,
            ))

    return "达到最大迭代次数，未能完成任务"


# ─── 测试入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    questions = [
        "火星和地球的直径差多少？",
        "如果一个正方形的边长是 15，它的面积是多少？",
        "月球直径是地球直径的百分之多少？",
    ]

    for q in questions:
        answer = run_langchain_agent(q)
        print(f"\n✅ 最终答案: {answer}")

    # ─── 对比总结 ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("框架对比: 手写 ReAct vs LangChain 1.x LCEL")
    print(f"{'='*60}")
    print("""
手写 SimpleReActAgent（experiments/agents/simple_react_agent.py）:
  ✅ 完全理解内部逻辑（学习必备）
  ✅ 可以完全定制控制流
  ❌ 用正则解析 "Action: tool[arg]" 文本，容易出错
  ❌ 代码量大

LangChain 1.x LCEL（本文件）:
  ✅ bind_tools() → LLM 直接输出 JSON 工具调用，更可靠
  ✅ @tool 装饰器自动生成 schema，不用手写字典
  ✅ 代码更简洁（核心逻辑约 20 行）
  ❌ 需要理解 LangChain 消息类型（HumanMessage/ToolMessage 等）

结论: 先手写理解原理 → 再用 LangChain 做生产项目
""")
