"""
工具的单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools import calculator, web_search, code_executor

def test_calculator():
    assert calculator("2 + 2") == "4"
    assert calculator("10 * 5") == "50"
    assert calculator("(10 + 5) * 2") == "30"
    assert "错误" in calculator("import os")
    print("✓ calculator 测试通过")

def test_web_search():
    result = web_search("火星直径")
    assert "6,779" in result
    result2 = web_search("未知话题xyz")
    assert "未找到" in result2
    print("✓ web_search 测试通过")

def test_code_executor():
    assert code_executor("2 + 2 * 3") == "8"
    assert "错误" in code_executor("import os")
    print("✓ code_executor 测试通过")

if __name__ == "__main__":
    test_calculator()
    test_web_search()
    test_code_executor()
    print("\n✓ 所有工具测试通过")
