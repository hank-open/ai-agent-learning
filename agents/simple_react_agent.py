"""
手写的 ReAct Agent
不使用框架，从零实现 ReAct 循环
目的: 理解 Agent 的工作原理
"""

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from agents.tools import TOOLS
import json
import re

client = Anthropic()


class SimpleReActAgent:
    def __init__(self, model="claude-haiku-4-5-20251001", max_iterations=10):
        self.model = model
        self.max_iterations = max_iterations
        self.conversation_history = []
        self.execution_trace = []

    def _build_system_prompt(self):
        tools_description = "\n".join([
            f"- {name}: {config['description']}"
            for name, config in TOOLS.items()
        ])
        print('tools_description:', tools_description)
        return f"""你是一个有用的 AI 助手。你可以使用以下工具：

{tools_description}

你必须严格遵循 ReAct 格式，每次只执行一个步骤：

Thought: 思考你需要做什么
Action: tool_name[参数]

或者，当问题已解决时：

Thought: 已经有足够信息了
Final Answer: 你的最终答案

规则：
- 每次回复只能包含一个 Action 或一个 Final Answer
- Action 格式必须严格是: Action: tool_name[参数]
- 得到 Observation 后再继续下一步"""

    def _parse_action(self, text: str):
        match = re.search(r'Action:\s*(\w+)\[([^\]]*)\]', text)
        if match:
            return match.group(1), match.group(2)
        return None, None

    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        if tool_name not in TOOLS:
            return f"错误: 未知工具 '{tool_name}'，可用工具: {list(TOOLS.keys())}"
        try:
            return TOOLS[tool_name]["function"](tool_input)
        except Exception as e:
            return f"工具执行错误: {str(e)}"

    def run(self, user_input: str) -> str:
        print(f"\n{'='*60}")
        print(f"用户问题: {user_input}")
        print(f"{'='*60}\n")

        self.conversation_history = [{"role": "user", "content": user_input}]
        self.execution_trace = []

        for iteration in range(self.max_iterations):
            print(f"--- 迭代 {iteration + 1} ---")

            response = client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self._build_system_prompt(),
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text
            print(f"Claude:\n{assistant_message}\n")

            step = {"iteration": iteration + 1, "response": assistant_message}

            tool_name, tool_input = self._parse_action(assistant_message)

            if tool_name:
                tool_result = self._execute_tool(tool_name, tool_input)
                print(f"工具结果: {tool_result}\n")

                step.update({"tool": tool_name, "input": tool_input, "result": tool_result})
                self.execution_trace.append(step)

                self.conversation_history.append({"role": "assistant", "content": assistant_message})
                self.conversation_history.append({"role": "user", "content": f"Observation: {tool_result}"})

            elif "Final Answer" in assistant_message:
                self.execution_trace.append(step)
                print("✓ Agent 完成\n")
                return assistant_message

            else:
                self.execution_trace.append(step)
                return assistant_message

        return f"⚠ 达到最大迭代次数 ({self.max_iterations})"

    def print_trace(self):
        print(f"\n{'='*60}")
        print("执行链路")
        print(f"{'='*60}")
        for step in self.execution_trace:
            if "tool" in step:
                print(f"迭代 {step['iteration']}: {step['tool']}({step['input']}) → {step['result']}")
            else:
                print(f"迭代 {step['iteration']}: Final Answer")


if __name__ == "__main__":
    agent = SimpleReActAgent()

    questions = [
        "火星和地球的直径差多少？",
        "如果一个正方形的边长是 15，它的面积是多少？",
    ]

    for q in questions:
        result = agent.run(q)
        agent.print_trace()
        print(f"\n最终答案: {result}\n{'='*60}\n")
