# AI Agent 工程师 - 核心技能矩阵与资源清单

## 技能矩阵地图

### 第一阶段：基础认知能力 (1-4周)

#### 1.1 LLM 基础理论
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **Transformer 架构** | 理解高层原理（不需深入数学） | 《Deep Learning 花书》CH2 / 3Blue1Brown 视频 | 看 Transformer 可视化，解释注意力机制 | 能用3分钟解释 Transformer 如何工作 |
| **Token & Context Window** | Token 定义、计费、长度限制 | OpenAI / Anthropic 官方文档 | 用 tiktoken 计算 token 数 | 能精确估算请求成本 |
| **温度/采样参数** | Temperature、Top-K、Top-P 含义 | LangChain 文档 + 实验 | 对比不同参数的输出差异 | 能选择合适参数优化输出 |
| **模型量化与成本** | 全精度 vs 量化、成本权衡 | GPTQ / AWQ / 4-bit 论文摘要 | 计算不同模型的成本/性能比 | 能评估是否应该用量化模型 |

**推荐学习路径:**
```
Week 1: LLM 基础 → 完成 1-2 个 LLM API 调用实验
        │
        └─ 阅读文档 + 看视频 (6h) → 实践 (4h) → 总结 (2h)

Week 2: Prompt 工程 → 对比 zero-shot vs few-shot vs CoT
        │
        └─ Zero-shot baseline (准确率X%) 
        └─ Few-shot baseline (准确率Y%)
        └─ CoT baseline (准确率Z%) 
        └─ 记录差异，理解为什么 CoT 更好

Week 3: Agent 认知 → 理解 ReAct 核心循环
        │
        └─ 阅读 ReAct 论文 (只读摘要和示例)
        └─ 手动走过一个 ReAct 循环 (Think → Act → Observe → Next)
        └─ 对比 Chain-of-Thought vs ReAct

Week 4: 向量和相似度 → 完成第一个 Embedding 实验
        │
        └─ 用 OpenAI API 计算句子 embedding
        └─ 计算欧几里得距离 + 余弦相似度
        └─ 理解为什么余弦相似度更好
```

#### 1.2 Prompt 工程
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **Zero-shot & Few-shot** | 理解样本数量对准确率的影响 | DeepLearning.AI Prompt 课程 | 实现 prompt 模板库 | 能为任意任务选择适当的 prompt 策略 |
| **Chain-of-Thought** | CoT、Self-Consistency、Tree-of-Thought | 论文 + 实验 | 手实现一个 CoT 推理器 | 能解释为什么 CoT 有效 |
| **角色扮演提示词** | 系统 prompt + 角色设定 | Anthropic 最佳实践文档 | 构建 3 个不同角色的 prompt | 能设计出高效的系统 prompt |
| **结构化输出** | JSON Schema、XML、Markdown | Claude API 文档 (structured output) | 设计一个通用输出格式定义器 | 能 100% 解析 LLM 的结构化输出 |

**核心 Prompt 模板:**
```python
# 模板 1: 基础 Q&A
"""
你是一个 {角色} 助手。
你的任务是 {任务描述}。
约束条件:
- {约束 1}
- {约束 2}

问题: {用户问题}
"""

# 模板 2: Chain-of-Thought
"""
请一步一步地思考这个问题。
步骤 1: {分析...}
步骤 2: {计算...}
步骤 3: {得出...}

最终答案: {结构化输出}
"""

# 模板 3: 角色扮演 Agent 提示词
"""
你是一个具有以下特征的 AI Assistant:
- 名称: {name}
- 专长: {expertise}
- 工具: {available_tools}
- 约束: {constraints}

当用户要求你执行任务时:
1. 分析用户需求
2. 选择合适的工具
3. 执行工具并观察结果
4. 根据结果改进策略
5. 提供最终答案

现在，用户说: {user_input}
"""
```

---

### 第二阶段：框架与工具 (5-12周)

#### 2.1 LangChain 框架
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **基本组件** | Model, Chain, Tool, Agent | LangChain 官方文档 + Python 快速入门 | 构建 Chain 链路 (4 步) | 能无文档写出基础 chain |
| **ReAct Agent** | 完整的 Agent 循环实现 | LangChain Agent 教程 | 实现一个 ReAct Agent (3个工具) | Agent 能自主调用工具解决问题 |
| **Prompts & Templates** | PromptTemplate、ChatPromptTemplate | 官方示例 | 构建动态 prompt 模板库 | 支持变量替换和条件 prompt |
| **Memory** | ConversationMemory、SummaryMemory | 文档 | 实现对话历史管理 | 能处理长对话（>100 轮） |

**LangChain 核心代码示例:**

```python
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain.prompts import PromptTemplate

# 定义工具
@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"错误: {e}"

@tool
def web_search(query: str) -> str:
    """搜索网络信息"""
    # 实现搜索逻辑 (可用 Google API 或 Tavily)
    pass

# 创建 Agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
tools = [calculator, web_search]

agent = create_react_agent(llm, tools)
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)

# 执行
result = executor.invoke({"input": "火星到地球的距离是多少？"})
print(result["output"])
```

#### 2.2 RAG 系统
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **文档加载与分块** | PyPDF, HTML, Markdown 加载 | LangChain 文档加载示例 | 加载 5 种文件格式 | 支持所有常见文档格式 |
| **Embedding & 向量化** | OpenAI/Anthropic Embedding | API 文档 | 计算 10K+ 文档的 embedding | 成本 < $10 |
| **向量数据库** | Pinecone, Weaviate, Milvus, PG | 数据库文档 | 搭建向量库 + 基本查询 | CRUD 操作无误 |
| **检索与重排** | BM25、混合搜索、重排序 | 向量库文档 + 论文 | 实现混合搜索 (dense + sparse) | 检索准确率 > 85% |
| **RAG 链路** | 完整的 retrieve → generate 流程 | LangChain RetrievalQA 教程 | 构建企业知识库 QA 系统 | 能回答知识库中的任意问题 |

**RAG Pipeline 代码:**

```python
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# 1. 加载与分块
loader = PyPDFLoader("company_policies.pdf")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "，", ""]
)
chunks = splitter.split_documents(documents)

# 2. Embedding & 存储
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Pinecone.from_documents(chunks, embeddings, index_name="policies")

# 3. 检索与生成
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 5}  # 返回最相关的 5 个文档
)
llm = ChatOpenAI(model="gpt-4", temperature=0)
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 或 "map_reduce", "refine"
    retriever=retriever,
    return_source_documents=True
)

# 4. 查询
result = qa({"query": "我们的休假政策是什么？"})
print(result["result"])
print("来源:", result["source_documents"])
```

#### 2.3 Function Calling / Tool Use
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **工具定义** | JSON Schema 格式定义 | OpenAI / Anthropic API 文档 | 定义 10 个工具的 schema | 所有工具都能被正确解析 |
| **工具路由** | 根据用户意图选择工具 | LangChain Agent 示例 | 实现自动工具选择 | 路由准确率 > 90% |
| **并行调用** | 同时调用多个工具 | 异步编程 + LangChain | 实现并行工具执行 | 速度提升 2-3 倍 |
| **错误处理** | 工具失败重试、备选方案 | 容错设计 | 实现智能重试机制 | 故障自动恢复率 > 95% |

**工具定义与调用:**

```python
import anthropic
import json

client = anthropic.Anthropic()

# 定义工具
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的当前天气",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，例如 '北京', '上海'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "温度单位"
                }
            },
            "required": ["location"]
        }
    },
    {
        "name": "search_flights",
        "description": "搜索航班",
        "input_schema": {
            "type": "object",
            "properties": {
                "from": {"type": "string", "description": "出发城市"},
                "to": {"type": "string", "description": "目的地城市"},
                "date": {"type": "string", "description": "出发日期 (YYYY-MM-DD)"}
            },
            "required": ["from", "to", "date"]
        }
    }
]

# 处理工具调用
def process_tool_call(tool_name, tool_input):
    if tool_name == "get_weather":
        # 实现天气查询逻辑
        return {"temperature": 25, "condition": "晴天"}
    elif tool_name == "search_flights":
        # 实现航班搜索逻辑
        return {"flights": [...]}

# Agent 循环
messages = [
    {"role": "user", "content": "我想去北京，请告诉我天气，然后帮我找航班"}
]

while True:
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )
    
    # 检查是否需要调用工具
    if response.stop_reason == "tool_use":
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        messages.append({"role": "assistant", "content": response.content})
        
        # 执行工具调用
        tool_results = []
        for tool_use in tool_uses:
            result = process_tool_call(tool_use.name, tool_use.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result)
            })
        
        messages.append({"role": "user", "content": tool_results})
    else:
        # Agent 完成，输出最终答案
        final_text = [block.text for block in response.content if hasattr(block, "text")]
        print("".join(final_text))
        break
```

---

### 第三阶段：核心工程化能力 (13-24周)

#### 3.1 可靠性设计
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **错误恢复** | 重试、降级、断路器 | 分布式系统设计 | 实现 3 层重试机制 | 成功率从 85% 提升到 99%+ |
| **输入验证** | 参数类型检查、范围验证 | Python Pydantic | 用 Pydantic 定义所有输入 | 100% 覆盖非法输入 |
| **超时管理** | request timeout、handler timeout | asyncio 文档 | 实现超时保护 | 无超时导致的挂起 |
| **降级策略** | 模型降级、工具降级 | 服务降级设计 | 实现多模型备选方案 | 主模型故障时自动切换 |

**错误处理代码示例:**

```python
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

class RobustAgent:
    def __init__(self, max_retries=3, timeout_seconds=30):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def call_llm_with_retry(self, prompt):
        """带重试的 LLM 调用"""
        try:
            response = await asyncio.wait_for(
                self.llm.agenerate([prompt]),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            # 降级到更快的模型
            return await self.llm_fast.agenerate([prompt])
    
    async def execute_tool_safely(self, tool_name, tool_input):
        """安全的工具执行"""
        try:
            # 验证输入
            validated_input = self.validate_tool_input(tool_name, tool_input)
            
            # 执行工具
            result = await asyncio.wait_for(
                self.tools[tool_name](validated_input),
                timeout=self.timeout_seconds
            )
            return result
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}")
            
            # 尝试备选工具
            alternative = self.find_alternative_tool(tool_name)
            if alternative:
                return await self.execute_tool_safely(alternative, tool_input)
            else:
                raise
```

#### 3.2 成本优化
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **Token 缓存** | Prompt 缓存、结果缓存 | Redis / 本地缓存 | 实现多层缓存 | 缓存命中率 > 40% |
| **模型选择** | 不同模型的成本/性能权衡 | 模型基准测试 | 建立成本矩阵 | 相同质量下成本降低 30-50% |
| **批量处理** | Batch API、异步处理 | API 文档 | 实现批量任务处理 | 吞吐量提升 5-10 倍 |
| **成本追踪** | Token 计数、成本报表 | Langfuse / LLMOps 工具 | 构建成本监控系统 | 精确到每个请求的成本 |

**成本优化实例:**

```python
import hashlib
from typing import Any
import json

class CostOptimizedAgent:
    def __init__(self):
        self.cache = {}  # 简单的内存缓存，生产环境用 Redis
        self.cost_log = []
        self.model_preference = {
            "simple": "gpt-4o-mini",      # 简单任务用便宜模型
            "medium": "gpt-4o",           # 中等任务
            "complex": "gpt-4-turbo"      # 复杂任务
        }
    
    def _get_cache_key(self, prompt: str) -> str:
        """计算 prompt hash 作为缓存 key"""
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    async def query_with_cache(self, prompt: str, task_complexity: str = "medium"):
        """带缓存和模型选择的查询"""
        cache_key = self._get_cache_key(prompt)
        
        # 检查缓存
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 选择模型
        model = self.model_preference.get(task_complexity, "gpt-4o")
        
        # 调用 LLM
        response = await self.llm.agenerate(
            [prompt],
            model=model
        )
        
        # 缓存结果
        self.cache[cache_key] = response
        
        # 记录成本
        self.cost_log.append({
            "model": model,
            "tokens": response.usage.total_tokens,
            "cost": self._estimate_cost(model, response.usage.total_tokens)
        })
        
        return response
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """估算成本"""
        pricing = {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03}
        }
        # 简化版，实际需要区分输入/输出 tokens
        rate = pricing.get(model, {}).get("input", 0)
        return rate * tokens / 1000
    
    def get_cost_report(self):
        """生成成本报告"""
        total_cost = sum(log["cost"] for log in self.cost_log)
        by_model = {}
        for log in self.cost_log:
            model = log["model"]
            if model not in by_model:
                by_model[model] = 0
            by_model[model] += log["cost"]
        
        return {
            "total_cost": total_cost,
            "by_model": by_model,
            "cache_hit_rate": len([x for x in self.cache.values()]) / max(len(self.cost_log), 1)
        }
```

#### 3.3 可观测性
| 技能点 | 掌握目标 | 学习资源 | 实践任务 | 验收标准 |
|------|---------|--------|--------|--------|
| **执行链路追踪** | 记录每一步的输入输出 | LLMOps 工具 (Langfuse) | 实现完整链路追踪 | 能复现任意失败的执行 |
| **性能监控** | 延迟、吞吐、错误率 | Prometheus + Grafana | 搭建监控面板 | 实时看到 99th latency |
| **成本监控** | Token 使用、API 调用量 | 自建或 LLM 平台提供 | 按天统计成本 | 预警当天费用超预算 |
| **日志聚合** | 结构化日志、集中管理 | ELK Stack / 云服务 | 实现结构化日志 | 任何错误都能通过日志查找 |

**可观测性代码:**

```python
import logging
from datetime import datetime
import json

class ObservableAgent:
    def __init__(self):
        self.setup_logging()
        self.execution_traces = []
    
    def setup_logging(self):
        """设置结构化日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("agent")
        
        # 添加 JSON 日志处理器用于上传到日志服务
        self.json_logger = logging.getLogger("agent.json")
    
    async def trace_execution(self, agent_name, step_name, inputs, outputs, duration_ms):
        """记录执行步骤"""
        trace = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "step": step_name,
            "inputs": inputs,
            "outputs": outputs,
            "duration_ms": duration_ms,
            "status": "success" if outputs else "failed"
        }
        
        self.execution_traces.append(trace)
        
        # JSON 结构化日志
        self.json_logger.info(json.dumps(trace))
        
        # 关键步骤日志
        if duration_ms > 5000:  # 超过 5 秒的步骤标记为警告
            self.logger.warning(f"Slow step: {step_name} took {duration_ms}ms")
    
    async def run_agent_with_observability(self, task):
        """带可观测性的 Agent 执行"""
        start_time = datetime.utcnow()
        
        try:
            # 执行第 1 步：理解任务
            step1_start = datetime.utcnow()
            understanding = await self.understand_task(task)
            step1_duration = (datetime.utcnow() - step1_start).total_seconds() * 1000
            await self.trace_execution("MainAgent", "understand_task", {"task": task}, understanding, step1_duration)
            
            # 执行第 2 步：规划
            step2_start = datetime.utcnow()
            plan = await self.create_plan(understanding)
            step2_duration = (datetime.utcnow() - step2_start).total_seconds() * 1000
            await self.trace_execution("MainAgent", "create_plan", understanding, plan, step2_duration)
            
            # 执行第 3 步：执行
            step3_start = datetime.utcnow()
            result = await self.execute_plan(plan)
            step3_duration = (datetime.utcnow() - step3_start).total_seconds() * 1000
            await self.trace_execution("MainAgent", "execute_plan", plan, result, step3_duration)
            
            # 总耗时
            total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.info(f"Agent execution completed in {total_duration}ms")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            # 记录失败链路
            await self.trace_execution("MainAgent", "error", {"task": task}, {"error": str(e)}, 
                                      (datetime.utcnow() - start_time).total_seconds() * 1000)
            raise
```

---

### 第四阶段：实战项目 (25-52周)

#### 4.1 项目 1: 智能客服 Agent
**难度: ⭐⭐ | 周期: 2-3 周**

**核心能力:**
- Multi-turn 对话管理
- 意图识别 + 工具路由
- 知识库集成 (FAQ RAG)
- 人工介入流程

**交付物清单:**
```
客服-Agent/
├── backend/
│   ├── agents/
│   │   ├── intent_classifier.py  (意图分类)
│   │   ├── resolver_agent.py      (问题解决 Agent)
│   │   └── escalation_handler.py  (升级处理)
│   ├── tools/
│   │   ├── faq_retriever.py       (FAQ 检索)
│   │   ├── order_lookup.py        (订单查询)
│   │   ├── ticket_creator.py      (创建工单)
│   │   └── email_sender.py        (发送邮件)
│   ├── rag/
│   │   ├── knowledge_base.py      (知识库管理)
│   │   └── embeddings.py          (Embedding 处理)
│   ├── api.py                     (FastAPI 服务)
│   └── config.py                  (配置管理)
├── frontend/
│   ├── ChatInterface.jsx          (聊天界面)
│   ├── AgentDebugger.jsx          (Agent 调试器)
│   └── styles/                    (样式)
├── tests/
│   ├── test_agents.py             (Agent 单元测试)
│   ├── test_tools.py              (工具测试)
│   └── test_rag.py                (RAG 测试)
├── docker-compose.yml             (本地部署)
└── README.md                       (项目文档)
```

**验收标准:**
- [ ] 支持 10+ 轮对话
- [ ] 意图识别准确率 > 90%
- [ ] FAQ 检索准确率 > 85%
- [ ] 人工介入流程完整
- [ ] 部署到 Docker，无报错
- [ ] API 端点完全文档化

**学习收获:**
1. Multi-turn 对话的状态管理
2. RAG 在实战中的优化技巧
3. 工具路由和降级策略
4. FastAPI 微服务开发
5. 错误处理和日志系统

---

#### 4.2 项目 2: 代码分析 Agent
**难度: ⭐⭐⭐ | 周期: 3-4 周**

**核心能力:**
- 文件系统访问和解析
- 代码静态分析
- 问题检测和修复建议
- 测试代码生成

**Agent 工作流:**

```
用户上传代码库
  ↓
[文件浏览 Agent]
  - 遍历文件结构
  - 识别项目类型 (React/Python/Node.js 等)
  ↓
[代码解析 Agent]
  - AST 解析关键文件
  - 提取函数、类、依赖
  ↓
[问题检测 Agent]
  - 检查常见问题 (性能、安全、风格)
  - 分析依赖和版本冲突
  ↓
[修复建议 Agent]
  - 生成具体改进建议
  - 提供代码片段
  ↓
[测试生成 Agent]
  - 生成单元测试代码
  - 提供测试覆盖率分析
  ↓
最终报告
```

**交付物:**
```
code-analyzer-agent/
├── agents/
│   ├── file_explorer.py           (文件浏览)
│   ├── code_parser.py             (代码解析)
│   ├── issue_detector.py          (问题检测)
│   ├── fix_suggester.py           (修复建议)
│   └── test_generator.py          (测试生成)
├── tools/
│   ├── ast_parser.py              (AST 解析)
│   ├── dependency_analyzer.py     (依赖分析)
│   ├── code_quality_checker.py    (代码质量)
│   └── security_scanner.py        (安全检查)
├── models/
│   └── analysis_result.py         (数据模型)
├── api.py                         (FastAPI)
├── requirements.txt               (依赖)
└── tests/
    └── test_analysis.py
```

**验收标准:**
- [ ] 支持 3+ 编程语言
- [ ] 检测常见代码问题 20+
- [ ] 生成的修复建议准确率 > 80%
- [ ] 测试生成覆盖率 > 70%
- [ ] API 响应时间 < 30s (5K LOC)
- [ ] 生成的测试代码能通过 linter

**学习收获:**
1. AST 和代码解析
2. 静态分析技术
3. 多个 Agent 的复杂协调
4. 大型代码库的处理
5. 实时流式处理

---

#### 4.3 项目 3: 数据分析 Agent
**难度: ⭐⭐⭐ | 周期: 3-4 周**

**核心能力:**
- SQL 代码生成和执行
- 数据探索和可视化
- 统计分析
- 自然语言查询

**数据流:**

```
自然语言查询
  ↓
[数据探索 Agent]
  - 获取表结构、字段类型
  - 样本数据预览
  ↓
[SQL 生成 Agent]
  - Text-to-SQL 模型生成查询
  - 语法验证
  ↓
[执行引擎]
  - 执行 SQL
  - 超时保护
  ↓
[可视化 Agent]
  - 选择最佳图表类型
  - 生成 JSON 图表定义
  ↓
[解释 Agent]
  - 用自然语言解释结果
  - 生成洞察
  ↓
最终答案 + 图表
```

**交付物:**
```
data-analyst-agent/
├── agents/
│   ├── data_explorer.py           (数据探索)
│   ├── sql_generator.py           (SQL 生成)
│   ├── visualizer.py              (可视化)
│   └── insight_generator.py       (洞察生成)
├── tools/
│   ├── database_connector.py      (数据库连接)
│   ├── sql_executor.py            (SQL 执行)
│   ├── chart_generator.py         (图表生成)
│   └── text_to_sql_model.py       (LLM 模型)
├── api.py                         (FastAPI)
├── requirements.txt               (依赖)
└── tests/
    └── test_analysis.py
```

**验收标准:**
- [ ] 支持 5+ 数据库类型
- [ ] SQL 生成正确率 > 85%
- [ ] 查询执行时间 < 10s
- [ ] 生成 5+ 种图表类型
- [ ] 可视化代码通过验证
- [ ] 自然语言解释清晰

**学习收获:**
1. Text-to-SQL 技术
2. 数据可视化设计
3. 数据库优化
4. 统计分析
5. 用户友好的数据呈现

---

#### 4.4 项目 4: 自主研究 Agent (可选高级项目)
**难度: ⭐⭐⭐⭐ | 周期: 4-6 周**

**核心能力:**
- 网页抓取和解析
- 多源信息融合
- 事实验证
- 结构化报告生成
- 多 Agent 协作

**Agent 协作架构:**

```
研究指令
  ↓
[Research Director Agent]
  - 分解研究问题
  - 规划研究步骤
  ↓ (并行)
┌─→ [Search Agent]        → 网页搜索
├─→ [Reader Agent]        → 内容提取
├─→ [Analyzer Agent]      → 数据分析
└─→ [Verifier Agent]      → 事实检验
  ↓ (汇聚)
[Synthesizer Agent]
  - 融合多个源的信息
  - 生成结构化报告
  ↓
最终研究报告
```

**核心挑战:**
- 信息的真实性和一致性
- 多源信息的融合
- 深度 vs 广度的权衡
- 成本控制（API 调用数）

---

## 学习资源总览

### 📚 必读书籍与论文
| 资源 | 类型 | 优先级 | 阅读时间 |
|------|------|------|--------|
| 《Designing ML Systems》- Chip Huyen | 书 | ⭐⭐⭐⭐⭐ | 20h |
| ReAct 论文 | 论文 | ⭐⭐⭐⭐ | 2h |
| LangChain 官方文档 | 文档 | ⭐⭐⭐⭐⭐ | 15h |
| Anthropic Prompt 最佳实践 | 文档 | ⭐⭐⭐⭐⭐ | 3h |
| RAG 论文汇总 | 论文 | ⭐⭐⭐ | 5h |

### 🎓 在线课程
- **DeepLearning.AI**: Prompt Engineering, LangChain
- **Coursera**: Building LLM Applications
- **YouTube**: Jeremy Zhang 的 AI Agent 系列

### 💻 开源项目（学习参考）
- **LangChain**: https://github.com/langchain-ai/langchain
- **LangGraph**: 状态机 Agent 框架
- **AutoGen**: Microsoft 的多 Agent 框架
- **CrewAI**: 高层 Agent 抽象

### 🛠️ 必装工具和库
```
核心库:
- langchain==0.1.0+
- langgraph==0.0.20+
- anthropic==0.7.0+
- openai==1.0.0+
- pydantic==2.0+

数据处理:
- pandas==2.0+
- numpy==1.24+
- scikit-learn==1.3+

向量库:
- pinecone-client==2.2+
- weaviate-client==3.20+
- milvus-connector==2.3+

工具:
- pytest==7.4+  (测试)
- black==23.0+  (代码格式)
- langfuse==0.1+ (可观测性)
```

### 🔗 关键文档链接
- OpenAI API: https://platform.openai.com/docs/api-reference
- Anthropic Claude: https://docs.anthropic.com
- LangChain: https://python.langchain.com/
- LangGraph: https://langchain-ai.github.io/langgraph/

---

## 学习节奏建议

### 每周时间分配（推荐 20-30h/周）
```
学习阶段 1-4 周 (基础):
- 理论学习: 40% (8h)
- 实践做项目: 50% (10h)
- 复习总结: 10% (2h)

学习阶段 5-12 周 (框架):
- 理论学习: 30% (6h)
- 实践做项目: 60% (12h)
- 复习总结: 10% (2h)

学习阶段 13-24 周 (工程化):
- 理论学习: 20% (4h)
- 实践做项目: 70% (14h)
- 复习总结: 10% (2h)

学习阶段 25-52 周 (实战项目):
- 项目开发: 80% (16h)
- 文档和优化: 20% (4h)
```

---

## 自我评估清单

### 完成度评分表
使用 1-5 分（1=完全不会，5=精通）进行自评：

| 技能点 | Week 4 | Week 12 | Week 24 | Week 52 |
|------|---------|----------|----------|----------|
| LLM 基础理论 | ___ | 5 | 5 | 5 |
| Prompt 工程 | 4 | 5 | 5 | 5 |
| Agent 架构 | 3 | 5 | 5 | 5 |
| LangChain | 0 | 4 | 5 | 5 |
| RAG 系统 | 0 | 4 | 5 | 5 |
| Tool Use | 0 | 3 | 5 | 5 |
| 错误处理 | 0 | 2 | 4 | 5 |
| 成本优化 | 0 | 2 | 4 | 5 |
| 可观测性 | 0 | 1 | 3 | 5 |
| 多 Agent 系统 | 0 | 0 | 2 | 4 |
| **总分** | **7** | **31** | **43** | **49** |

目标: Week 52 达到 45+ 分

---

**最后更新**: 2026/04/02
**作者**: Claude
**持续维护中**...
