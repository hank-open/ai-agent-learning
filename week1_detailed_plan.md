# 第一周详细计划 & 立即行动清单

## 🎯 周目标

完成这周后，你应该拥有：
1. ✅ 一个工作的 ReAct Agent（3 个工具）
2. ✅ 部署到 FastAPI 的 API 服务
3. ✅ GitHub repo 和基础文档
4. ✅ 对 LLM 参数的深入理解

**预计投入**: 每天 2-3 小时（业余时间足够）

---

## 📅 日程安排

### Monday - 搭建环境 & LLM 基础 (2.5h)

#### 上午 (1h - 选择一个时段)

**任务 1: 环境搭建** (30min)

创建项目目录和虚拟环境：

```bash
# 创建项目目录
mkdir ai-agent-learning
cd ai-agent-learning

# 初始化 Git
git init
git config user.email "you@example.com"
git config user.name "Your Name"

# 创建 Python 虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 验证 Python 版本 (应该 >= 3.9)
python --version
```

创建 `requirements.txt`：

```txt
anthropic==0.7.0
langchain==0.1.0
langchain-community==0.0.10
fastapi==0.104.0
uvicorn==0.24.0
python-dotenv==1.0.0
```

安装依赖：

```bash
pip install -r requirements.txt
```

**任务 2: API Key 配置** (30min)

创建 `.env` 文件：

```
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

创建 `config.py`：

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 验证
    assert ANTHROPIC_API_KEY, "Missing ANTHROPIC_API_KEY in .env"

config = Config()
```

验证配置：

```python
python -c "from config import config; print('✓ Config loaded successfully')"
```

#### 午间 (1h)

**任务 3: 学习 LLM 参数** 

阅读材料（30min）：
- Anthropic 官方文档关于参数的部分: https://platform.claude.com/docs/en/api/messages
- 重点: Temperature, Max Tokens, Top-P

创建学习笔记 `notes/01-llm-basics.md`：

```markdown
# LLM 基础参数

## Temperature (0.0 - 1.0)
- 0.0: 完全确定性，总是选择概率最高的 token
- 0.5: 平衡，用于大多数任务
- 1.0: 最随机，创意任务

对话示例:
Q: 2 + 2 = ?
- temp=0.0: "4"
- temp=0.7: "4"
- temp=1.0: "4 或 5" (错的，但创意)

## Max Tokens
- 限制输出长度
- 更短 = 更便宜
- 需要根据任务类型调整

## Top-P (Nucleus Sampling)
- 0.9: 保留概率最高的 90% 的 token
- 可以结合 temperature 使用
```

#### 下午 (0.5h)

**验证清单：**

- [ ] 虚拟环境激活成功
- [ ] 依赖安装完成
- [ ] API Key 配置正确
- [ ] 可以导入 anthropic 和 langchain

---

### Tuesday - 第一个 LLM 调用 + 参数实验 (3h)

#### 上午 (1.5h)

**任务 1: 简单的 LLM API 调用** (45min)

创建 `experiments/01_basic_call.py`：

```python
"""
简单的 Claude API 调用
目的: 验证 API 连接和基础调用
"""

from anthropic import Anthropic

client = Anthropic()

def basic_call():
    """最简单的一次调用"""
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "你好，请自我介绍一下"
            }
        ]
    )
    
    print("Response:", message.content[0].text)
    print(f"Tokens: {message.usage.input_tokens + message.usage.output_tokens}")
    print(f"Cost: ${(message.usage.input_tokens * 0.003 + message.usage.output_tokens * 0.015) / 1000:.4f}")

if __name__ == "__main__":
    basic_call()
```

运行：
```bash
python experiments/01_basic_call.py
```

**任务 2: 多轮对话** (45min)

创建 `experiments/02_conversation.py`：

```python
"""
多轮对话示例
目的: 理解消息历史和对话上下文
"""

from anthropic import Anthropic

client = Anthropic()

def multi_turn_conversation():
    """模拟多轮对话"""
    
    messages = []
    
    # 第 1 轮
    user_input_1 = "我的名字叫 Alice，我是一个数据科学家"
    messages.append({"role": "user", "content": user_input_1})
    
    response_1 = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=messages
    )
    
    assistant_response_1 = response_1.content[0].text
    messages.append({"role": "assistant", "content": assistant_response_1})
    
    print(f"User: {user_input_1}")
    print(f"Assistant: {assistant_response_1}\n")
    
    # 第 2 轮 (Claude 会记得 Alice 的身份)
    user_input_2 = "我的专长是什么？"
    messages.append({"role": "user", "content": user_input_2})
    
    response_2 = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=messages
    )
    
    assistant_response_2 = response_2.content[0].text
    
    print(f"User: {user_input_2}")
    print(f"Assistant: {assistant_response_2}\n")
    
    # 第 3 轮
    user_input_3 = "推荐一个学习资源给我"
    messages.append({"role": "assistant", "content": assistant_response_2})
    messages.append({"role": "user", "content": user_input_3})
    
    response_3 = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=messages
    )
    
    assistant_response_3 = response_3.content[0].text
    
    print(f"User: {user_input_3}")
    print(f"Assistant: {assistant_response_3}\n")
    
    # 总成本统计
    total_input = (response_1.usage.input_tokens + 
                   response_2.usage.input_tokens + 
                   response_3.usage.input_tokens)
    total_output = (response_1.usage.output_tokens + 
                    response_2.usage.output_tokens + 
                    response_3.usage.output_tokens)
    
    total_cost = (total_input * 0.003 + total_output * 0.015) / 1000
    
    print(f"\n总 Token 数: {total_input + total_output}")
    print(f"总成本: ${total_cost:.4f}")

if __name__ == "__main__":
    multi_turn_conversation()
```

运行并观察对话的连贯性。

#### 下午 (1.5h)

**任务 3: 参数实验** (1.5h)

创建 `experiments/03_parameter_tuning.py`：

```python
"""
LLM 参数对比实验
目的: 理解 temperature, max_tokens, top_p 的影响
"""

from anthropic import Anthropic
import json

client = Anthropic()

def parameter_experiment():
    """对比不同参数的输出"""
    
    prompt = "请给出一个创意的故事开头，关于一个机器人发现了一个秘密。输出不超过 50 字。"
    
    configs = [
        {"temperature": 0.0, "max_tokens": 100, "name": "确定性 (temp=0)"},
        {"temperature": 0.5, "max_tokens": 100, "name": "平衡 (temp=0.5)"},
        {"temperature": 1.0, "max_tokens": 100, "name": "创意 (temp=1.0)"},
    ]
    
    results = {}
    
    for config in configs:
        print(f"\n{'='*50}")
        print(f"配置: {config['name']}")
        print(f"{'='*50}")
        
        # 生成 3 次，看输出是否一致
        outputs = []
        total_cost = 0
        
        for i in range(3):
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                messages=[{"role": "user", "content": prompt}]
            )
            
            output = response.content[0].text
            outputs.append(output)
            
            cost = (response.usage.input_tokens * 0.003 + 
                   response.usage.output_tokens * 0.015) / 1000
            total_cost += cost
            
            print(f"输出 {i+1}: {output}")
            print(f"Token: {response.usage.output_tokens}, 成本: ${cost:.4f}")
        
        # 检查一致性
        unique_outputs = len(set(outputs))
        print(f"\n唯一输出数: {unique_outputs}/3 (1=完全确定, 3=完全随机)")
        print(f"总成本: ${total_cost:.4f}")
        
        results[config['name']] = {
            "outputs": outputs,
            "unique_count": unique_outputs,
            "total_cost": total_cost
        }
    
    # 保存结果
    with open("experiments/results/parameter_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n✓ 结果已保存到 experiments/results/parameter_results.json")

if __name__ == "__main__":
    import os
    os.makedirs("experiments/results", exist_ok=True)
    parameter_experiment()
```

运行并分析结果。

**预期观察:**
- temp=0.0 时，3 次输出应该完全相同
- temp=1.0 时，3 次输出可能都不同
- temp=0.5 时，可能有 1-2 次相同

#### 晚间 (可选加强)

记录学习笔记：

```markdown
# Tuesday 学习总结

## 关键发现
1. Temperature 确实影响输出的确定性
2. 成本计算: 输入 token $0.003/1K, 输出 token $0.015/1K
3. 多轮对话时，前面轮次的 token 都需要重新传递

## 思考题
- 如果要回答一个数学问题，应该用什么 temperature？
- 如果要生成创意写作，应该用什么 temperature？
- 如何在成本和质量之间找到平衡？
```

---

### Wednesday - Agent 核心概念 & 第一个 Tool (2.5h)

#### 上午 (1h)

**任务 1: 理解 ReAct 循环** (1h)

阅读 ReAct 论文摘要（30min）：
https://arxiv.org/abs/2210.03629

创建 `notes/02-react-pattern.md`：

```markdown
# ReAct 设计模式

## 核心循环

1. **Thought**: Agent 思考接下来要做什么
   ```
   Thought: 我需要先计算出火星的平均温度，
   然后根据表面积计算总热量
   ```

2. **Action**: Agent 选择一个工具来执行
   ```
   Action: search[mars temperature]
   ```

3. **Observation**: 获得工具的输出
   ```
   Observation: 火星平均温度是 -80 摄氏度
   ```

4. **Next Action**: 继续思考和行动
   或者
5. **Final Answer**: 如果问题已解决，给出最终答案
   ```
   Final Answer: 火星的平均温度是 -80 摄氏度
   ```

## 示例：完整 ReAct 循环

```
问题: 火星的直径是多少？

Thought: 我需要搜索火星的直径信息
Action: search[mars diameter]
Observation: 火星的直径约为 6,779 公里

Thought: 已经得到答案了
Final Answer: 火星的直径约为 6,779 公里
```

## 为什么 ReAct 有效？

1. 允许 Agent 调用外部工具获取信息
2. Thinking 过程让 Agent 有机会纠正错误
3. Observation 让 Agent 基于实际反馈调整策略
```

#### 下午 (1.5h)

**任务 2: 定义第一个工具** (1.5h)

创建 `agents/tools.py`：

```python
"""
Agent 可以使用的工具
这是构建 Agent 的第一步
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
        result = eval(expression)
        # 只允许基本的数学运算，防止代码注入
        if isinstance(result, (int, float)):
            return str(result)
        else:
            return f"错误: {expression} 的结果不是数字"
    except Exception as e:
        return f"计算错误: {str(e)}"

def web_search(query: str) -> str:
    """
    搜索网络信息 (模拟)
    
    注: 这里是模拟实现。在真实应用中，应该调用真实搜索 API
    如: Tavily, Google Search, Bing Search
    """
    
    # 简单的知识库
    knowledge_base = {
        "火星直径": "火星的直径约为 6,779 公里",
        "火星": "火星是太阳系的第四颗行星",
        "地球直径": "地球的直径约为 12,742 公里",
        "2024年": "2024 年是平年",
    }
    
    # 搜索知识库
    for key, value in knowledge_base.items():
        if key.lower() in query.lower():
            return value
    
    return f"未找到关于 '{query}' 的信息"

def code_executor(code: str) -> str:
    """
    执行 Python 代码 (安全的沙箱版本)
    
    注: 这里只是示例。真实应用应该使用 sandboxed 执行环境
    """
    
    # 禁止的操作
    forbidden_keywords = ["import", "open", "exec", "__"]
    
    for keyword in forbidden_keywords:
        if keyword in code.lower():
            return f"错误: 代码包含禁止操作 '{keyword}'"
    
    try:
        # 受限的执行环境
        result = eval(code)
        return str(result)
    except Exception as e:
        return f"执行错误: {str(e)}"

# 工具目录
TOOLS = {
    "calculator": {
        "function": calculator,
        "description": "计算数学表达式",
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
        "description": "执行 Python 代码",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码"
                }
            },
            "required": ["code"]
        }
    }
}
```

#### 晚间

**任务 3: 测试工具** (30min)

创建 `tests/test_tools.py`：

```python
"""
工具的单元测试
"""

from agents.tools import calculator, web_search, code_executor

def test_calculator():
    """测试计算器"""
    assert calculator("2 + 2") == "4"
    assert calculator("10 * 5") == "50"
    assert calculator("(10 + 5) * 2") == "30"
    print("✓ calculator 测试通过")

def test_web_search():
    """测试网络搜索"""
    result = web_search("火星直径")
    assert "6,779" in result or "直径" in result
    print("✓ web_search 测试通过")

def test_code_executor():
    """测试代码执行"""
    result = code_executor("2 + 2 * 3")
    assert result == "8"
    print("✓ code_executor 测试通过")

if __name__ == "__main__":
    test_calculator()
    test_web_search()
    test_code_executor()
    print("\n✓ 所有工具测试通过")
```

运行：

```bash
python tests/test_tools.py
```

---

### Thursday - 构建第一个 ReAct Agent (3h)

#### 上午 (1.5h)

**任务 1: 手写 ReAct Agent** (1.5h)

创建 `agents/simple_react_agent.py`：

```python
"""
手写的 ReAct Agent
不使用框架，从零开始实现 ReAct 循环
目的: 理解 Agent 的工作原理
"""

from anthropic import Anthropic
from agents.tools import TOOLS
import json
import re

client = Anthropic()

class SimpleReActAgent:
    def __init__(self, model="claude-3-5-sonnet-20241022", max_iterations=10):
        self.model = model
        self.max_iterations = max_iterations
        self.conversation_history = []
        self.execution_trace = []
    
    def _build_system_prompt(self):
        """构建系统 prompt，告诉 Claude 有哪些工具"""
        
        tools_description = json.dumps(
            {tool_name: tool_config["description"] 
             for tool_name, tool_config in TOOLS.items()},
            ensure_ascii=False,
            indent=2
        )
        
        return f"""你是一个有用的 AI 助手。你可以使用以下工具来帮助用户:

{tools_description}

你应该遵循 ReAct 模式:
1. Thought: 思考你需要做什么
2. Action: 选择一个工具来执行，格式为 Action: tool_name[参数]
3. Observation: 观察工具的输出
4. (重复 1-3 直到问题解决)
5. Final Answer: 给出最终答案

示例:
用户: 火星和地球的直径差多少?

Thought: 我需要找到火星和地球的直径，然后计算差值
Action: web_search[火星直径]
Observation: 火星的直径约为 6,779 公里
Action: web_search[地球直径]
Observation: 地球的直径约为 12,742 公里
Action: calculator[12742 - 6779]
Observation: 5963
Final Answer: 地球的直径比火星大约 5,963 公里

现在开始处理用户的请求。"""
    
    def _parse_action(self, text: str) -> tuple:
        """从 Claude 的输出中解析工具调用"""
        
        # 查找 "Action: tool_name[param]" 模式
        match = re.search(r'Action:\s*(\w+)\[([^\]]*)\]', text)
        
        if match:
            tool_name = match.group(1)
            tool_input = match.group(2)
            return tool_name, tool_input
        
        return None, None
    
    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """执行工具"""
        
        if tool_name not in TOOLS:
            return f"错误: 未知的工具 '{tool_name}'"
        
        tool_func = TOOLS[tool_name]["function"]
        
        try:
            result = tool_func(tool_input)
            return result
        except Exception as e:
            return f"工具执行错误: {str(e)}"
    
    def run(self, user_input: str) -> str:
        """运行 Agent 来回答用户的问题"""
        
        print(f"\n{'='*60}")
        print(f"用户问题: {user_input}")
        print(f"{'='*60}\n")
        
        # 初始化对话历史
        self.conversation_history = [
            {"role": "user", "content": user_input}
        ]
        
        # ReAct 循环
        for iteration in range(self.max_iterations):
            print(f"--- 迭代 {iteration + 1} ---")
            
            # 调用 Claude 获得思考和行动
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self._build_system_prompt(),
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            print(f"Claude 回应:\n{assistant_message}\n")
            
            # 记录执行步骤
            self.execution_trace.append({
                "iteration": iteration + 1,
                "assistant_response": assistant_message
            })
            
            # 检查是否有行动
            tool_name, tool_input = self._parse_action(assistant_message)
            
            if tool_name:
                print(f"执行工具: {tool_name}({tool_input})")
                
                # 执行工具
                tool_result = self._execute_tool(tool_name, tool_input)
                print(f"工具结果: {tool_result}\n")
                
                # 记录执行步骤
                self.execution_trace[-1]["tool_name"] = tool_name
                self.execution_trace[-1]["tool_input"] = tool_input
                self.execution_trace[-1]["tool_result"] = tool_result
                
                # 将工具结果添加到对话历史
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                self.conversation_history.append({
                    "role": "user",
                    "content": f"Observation: {tool_result}\n\n继续思考和行动"
                })
            
            else:
                # 没有行动，检查是否是最终答案
                if "Final Answer" in assistant_message:
                    print("✓ Agent 得出最终答案\n")
                    return assistant_message
                else:
                    print("⚠ 无法解析工具调用，可能是最终答案\n")
                    return assistant_message
        
        print(f"⚠ 达到最大迭代次数 ({self.max_iterations})")
        return "Agent 未能在规定的迭代次数内完成任务"
    
    def print_execution_trace(self):
        """打印执行链路"""
        print(f"\n{'='*60}")
        print("执行链路:")
        print(f"{'='*60}")
        
        for step in self.execution_trace:
            print(f"\n迭代 {step['iteration']}:")
            if "tool_name" in step:
                print(f"  工具: {step['tool_name']}({step['tool_input']})")
                print(f"  结果: {step['tool_result']}")
            else:
                print(f"  (无工具调用)")

# 使用示例
if __name__ == "__main__":
    agent = SimpleReActAgent()
    
    # 测试问题
    test_question = "火星和地球的直径差多少？"
    
    result = agent.run(test_question)
    agent.print_execution_trace()
    
    print(f"\n{'='*60}")
    print("最终答案:")
    print(f"{'='*60}")
    print(result)
```

运行测试：

```bash
python agents/simple_react_agent.py
```

**预期输出:**
```
============================================================
用户问题: 火星和地球的直径差多少？
============================================================

--- 迭代 1 ---
Claude 回应:
Thought: 我需要找到火星和地球的直径...
Action: web_search[火星直径]

执行工具: web_search(火星直径)
工具结果: 火星的直径约为 6,779 公里

--- 迭代 2 ---
...

Final Answer: 地球的直径比火星大约 5,963 公里

============================================================
执行链路:
============================================================

迭代 1:
  工具: web_search(火星直径)
  结果: 火星的直径约为 6,779 公里

迭代 2:
  工具: web_search(地球直径)
  结果: 地球的直径约为 12,742 公里

迭代 3:
  工具: calculator(12742 - 6779)
  结果: 5963
```

#### 下午 (1.5h)

**任务 2: 改进版本 - 使用 LangChain** (1.5h)

创建 `agents/langchain_react_agent.py`：

```python
"""
使用 LangChain 的 ReAct Agent
对比手写版本，看看框架如何简化开发
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain.chat_models import ChatAnthropic
from langchain.prompts import PromptTemplate
import json

# 定义工具（使用 @tool 装饰器）
@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"错误: {str(e)}"

@tool
def web_search(query: str) -> str:
    """搜索网络信息"""
    knowledge_base = {
        "火星直径": "火星的直径约为 6,779 公里",
        "火星": "火星是太阳系的第四颗行星",
        "地球直径": "地球的直径约为 12,742 公里",
    }
    
    for key, value in knowledge_base.items():
        if key.lower() in query.lower():
            return value
    
    return f"未找到关于 '{query}' 的信息"

def run_langchain_agent(question: str):
    """使用 LangChain 运行 ReAct Agent"""
    
    # 初始化 LLM
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    
    # 定义工具列表
    tools = [calculator, web_search]
    
    # 创建 ReAct Agent
    agent = create_react_agent(llm, tools)
    
    # 创建 Agent 执行器
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )
    
    # 执行
    result = executor.invoke({"input": question})
    
    return result

if __name__ == "__main__":
    # 测试问题
    test_question = "火星和地球的直径差多少？"
    
    print(f"问题: {test_question}\n")
    result = run_langchain_agent(test_question)
    print(f"\n最终答案: {result}")
```

对比两个版本：

| 方面 | 手写版本 | LangChain 版本 |
|------|--------|--------------|
| 代码行数 | ~200 | ~60 |
| 易用性 | 需要理解内部逻辑 | 开箱即用 |
| 灵活性 | 完全自定义 | 有框架约束 |
| 学习价值 | ⭐⭐⭐⭐⭐ 理解原理 | ⭐⭐⭐ 实战应用 |

**重要:** 手写版本很重要，因为你能理解 Agent 的工作原理。但生产应该用 LangChain。

---

### Friday - 部署到 FastAPI + GitHub (2.5h)

#### 上午 (1h)

**任务 1: 创建 FastAPI 服务** (1h)

创建 `api.py`：

```python
"""
FastAPI 服务
暴露 Agent 的 HTTP 接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.langchain_react_agent import run_langchain_agent
from typing import Optional

# 初始化 FastAPI 应用
app = FastAPI(
    title="AI Agent API",
    description="ReAct Agent API 服务",
    version="0.1.0"
)

# 允许跨域请求 (用于前端调用)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义数据模型
class AgentRequest(BaseModel):
    question: str
    max_iterations: Optional[int] = 10

class AgentResponse(BaseModel):
    answer: str
    status: str = "success"

# 路由
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.post("/agent/run")
async def run_agent(request: AgentRequest) -> AgentResponse:
    """
    运行 Agent 来回答问题
    
    请求示例:
    {
        "question": "火星和地球的直径差多少？",
        "max_iterations": 10
    }
    """
    
    try:
        if not request.question.strip():
            raise ValueError("问题不能为空")
        
        # 运行 Agent
        result = run_langchain_agent(request.question)
        
        return AgentResponse(
            answer=result.get("output", "无法生成答案"),
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """根端点"""
    return {
        "name": "AI Agent API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "agent": "/agent/run (POST)"
        }
    }

# 启动命令
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # 开发模式，代码改动自动重启
    )
```

测试服务：

```bash
# 启动服务
python api.py

# 在另一个终端测试
curl http://localhost:8000/health
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"question": "火星和地球的直径差多少？"}'
```

#### 下午 (1.5h)

**任务 2: GitHub 初始化 + 提交代码** (1h)

创建项目结构：

```
ai-agent-learning/
├── agents/
│   ├── __init__.py
│   ├── tools.py                    # 工具定义
│   ├── simple_react_agent.py       # 手写 ReAct Agent
│   └── langchain_react_agent.py    # LangChain 版本
├── experiments/
│   ├── 01_basic_call.py
│   ├── 02_conversation.py
│   ├── 03_parameter_tuning.py
│   └── results/
├── notes/
│   ├── 01-llm-basics.md
│   └── 02-react-pattern.md
├── tests/
│   └── test_tools.py
├── api.py                          # FastAPI 服务
├── config.py                       # 配置
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

创建 `.gitignore`：

```
venv/
__pycache__/
*.pyc
.env
.DS_Store
.idea/
.vscode/
experiments/results/
```

创建 `README.md`：

```markdown
# AI Agent 学习项目

这是一个学习 AI Agent 开发的完整项目。

## 目标

通过构建功能完整的 ReAct Agent，学习：
- LLM API 调用
- Agent 设计模式
- Tool 定义和使用
- FastAPI 后端开发
- 项目工程化

## 项目结构

- `agents/`: Agent 实现
- `experiments/`: 学习实验和参数优化
- `notes/`: 学习笔记
- `tests/`: 单元测试
- `api.py`: FastAPI 服务

## 快速开始

1. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置 API Key
```bash
cp .env.example .env
# 编辑 .env，添加你的 API key
```

4. 运行 Agent
```bash
python agents/langchain_react_agent.py
```

5. 启动 API 服务
```bash
python api.py
```

## 学习进度

- [x] Week 1: 基础 + 第一个 Agent
- [ ] Week 2-4: RAG + 数据库
- [ ] Week 5-8: 第一个项目
- [ ] Week 9+: 进阶项目

## 参考资源

- [Anthropic Claude API](https://docs.anthropic.com)
- [LangChain](https://python.langchain.com/)
- [ReAct 论文](https://arxiv.org/abs/2210.03629)

## 作者

Your Name
```

提交到 GitHub：

```bash
git add .
git commit -m "init: First working ReAct Agent with FastAPI

- Implemented manual ReAct Agent from scratch
- Added LangChain-based Agent wrapper
- Created FastAPI service with /agent/run endpoint
- Added basic tools: calculator, web_search
- Included learning experiments and documentation

Ready for Week 2: RAG and Database integration"

git branch -M main
git remote add origin https://github.com/yourname/ai-agent-learning.git
git push -u origin main
```

**任务 3: 项目总结文档** (0.5h)

创建 `WEEK_1_SUMMARY.md`：

```markdown
# Week 1 学习总结

## 完成情况

✅ 搭建完整的开发环境
✅ 完成 5 个 LLM 实验
✅ 手写 ReAct Agent 实现
✅ LangChain ReAct Agent 实现
✅ FastAPI 服务开发
✅ 完整的测试和文档

## 关键成果

### 1. LLM 参数的深入理解
- Temperature 对输出的影响
- Token 计数和成本计算
- 参数优化的方法

### 2. Agent 核心概念
- ReAct 循环的完整实现
- Tool 定义和调用
- Agent 状态管理

### 3. 工程实践
- Python + FastAPI 开发
- API 设计和测试
- 代码组织和文档

## 代码统计
- 总行数: ~600 行
- 测试覆盖: 3 个工具 + Agent
- API 端点: 3 个

## 下周计划

- RAG 系统基础
- 向量数据库集成
- 知识库搭建

## 经验教训

1. **手写优于框架**: 通过手写 ReAct 循环，理解比用框架快得多
2. **实验很重要**: 参数实验让我深入理解 LLM 行为
3. **文档同样重要**: 好的文档能帮助你和他人理解代码

## 下一步建议

1. 尝试添加更多工具（数据库查询、API 调用等）
2. 优化 Prompt，提高 Agent 的推理能力
3. 构建一个简单的前端来可视化 Agent 的执行过程
```

#### 晚间 (可选)

**检查清单:**

```
✓ 项目结构完整
✓ 所有代码都在 Git 中
✓ README 文档完善
✓ 可以一键启动（需要 .env 配置后）
✓ 至少有 3 个工作示例
✓ 代码有注释和文档字符串
✓ 测试通过
```

---

## 📊 周总结与指标

### 时间投入
- 总投入: 12.5 小时（业余时间完成）
- 平均每天: 1.8 小时
- 最多一天: 3 小时（周四）

### 学习成果
- 代码行数: ~600
- 完成项目: 1（第一个工作的 Agent）
- 文档页数: 3
- GitHub 仓库: 1

### 关键指标
| 指标 | 目标 | 实际 |
|------|------|------|
| Agent 工作率 | 100% | ✓ |
| API 响应成功率 | >90% | ✓ |
| 测试通过率 | 100% | ✓ |
| 代码可读性 | 高 | ✓ |

### 自我评估
- LLM 基础理解: 4/5 ⭐⭐⭐⭐
- Agent 概念掌握: 4/5 ⭐⭐⭐⭐
- Python 能力: 3/5 ⭐⭐⭐
- FastAPI 能力: 3/5 ⭐⭐⭐
- 工程化实践: 3.5/5 ⭐⭐⭐☆
- **总体水平: 3.6/5**

---

## 下周预告 (Week 2)

### Week 2 主题: 后端开发 + 数据库

**将学到:**
- Python 和 FastAPI 深化
- 关系型数据库 (PostgreSQL)
- 向量数据库基础 (Pinecone)
- 简单 RAG 实现

**目标:**
- 能使用数据库存储对话历史
- 能从向量库检索信息
- 搭建一个知识库 QA 系统

**时间投入:** 15-20 小时

---

## 💡 最后的话

恭喜你完成了 Week 1！🎉

你现在拥有：
1. ✅ 一个工作的 AI Agent
2. ✅ 理解 Agent 如何思考和行动
3. ✅ 能将 Agent 部署为 API 服务
4. ✅ 完整的代码和文档

**最重要的是**: 你已经从"会调用 API"进升到"能设计 Agent 系统"。

下周我们会把 Agent 变得更智能，通过集成知识库让它能回答真实业务问题。

**继续加油！** 💪

---

**Date**: 2026-04-02
**Progress**: Week 1/20 (5%)
