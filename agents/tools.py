"""
Agent 可以使用的工具
"""

def calculator(expression: str) -> str:
    """
    计算数学表达式

    示例:
    - calculator("2 + 2") -> "4"
    - calculator("10 * 5") -> "50"
    - calculator("(10 + 5) * 2") -> "30"
    """
    try:
        # 只允许数字和基本运算符，防止代码注入
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return f"错误: 表达式包含非法字符"
        result = eval(expression)
        if isinstance(result, (int, float)):
            return str(result)
        return f"错误: {expression} 的结果不是数字"
    except Exception as e:
        return f"计算错误: {str(e)}"


def web_search(query: str) -> str:
    """
    搜索网络信息（模拟）

    注: 真实应用中应调用 Tavily / Google Search API
    """
    knowledge_base = {
        "火星直径": "火星的直径约为 6,779 公里",
        "火星":     "火星是太阳系的第四颗行星，平均温度约 -80°C",
        "地球直径": "地球的直径约为 12,742 公里",
        "地球":     "地球是太阳系的第三颗行星，表面积约 5.1 亿平方公里",
        "2024年":   "2024 年是闰年，共 366 天",
    }

    for key, value in knowledge_base.items():
        if key.lower() in query.lower():
            return value

    return f"未找到关于 '{query}' 的信息"


def code_executor(code: str) -> str:
    """
    执行简单的 Python 表达式（受限沙箱）

    注: 仅支持纯表达式，禁止 import / open 等操作
    """
    forbidden = ["import", "open", "exec", "eval", "__", "os", "sys"]
    for kw in forbidden:
        if kw in code.lower():
            return f"错误: 代码包含禁止操作 '{kw}'"

    try:
        result = eval(code)
        return str(result)
    except Exception as e:
        return f"执行错误: {str(e)}"


# 工具注册表（供 Agent 使用）
TOOLS = {
    "calculator": {
        "function": calculator,
        "description": "计算数学表达式，如 '2 + 2 * 3'",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2 + 2 * 3'"
                }
            },
            "required": ["expression"]
        }
    },
    "web_search": {
        "function": web_search,
        "description": "搜索网络信息",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    },
    "code_executor": {
        "function": code_executor,
        "description": "执行简单的 Python 表达式",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 表达式"
                }
            },
            "required": ["code"]
        }
    }
}
