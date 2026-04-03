# ReAct 设计模式

## 核心循环

1. **Thought**: Agent 思考接下来要做什么
2. **Action**: Agent 选择一个工具来执行
3. **Observation**: 获得工具的输出
4. 重复 1-3，直到问题解决
5. **Final Answer**: 给出最终答案

## 示例：完整 ReAct 循环

```
问题: 火星和地球的直径差多少？

Thought: 我需要找到火星和地球的直径，然后计算差值
Action: web_search[火星直径]
Observation: 火星的直径约为 6,779 公里

Thought: 还需要地球直径
Action: web_search[地球直径]
Observation: 地球的直径约为 12,742 公里

Thought: 现在可以计算差值了
Action: calculator[12742 - 6779]
Observation: 5963

Final Answer: 地球的直径比火星大约 5,963 公里
```

## 为什么 ReAct 有效？

1. **工具调用**：允许 Agent 获取外部信息，突破 LLM 知识截止日期的限制
2. **显式推理**：Thought 步骤让 Agent 有机会规划和纠正
3. **基于反馈**：Observation 让 Agent 根据真实结果调整策略，而不是凭空猜测

## 与普通 LLM 调用的区别

| 普通调用 | ReAct Agent |
|---------|------------|
| 一次性回答 | 多步推理 |
| 依赖训练数据 | 可调用实时工具 |
| 无法纠错 | 观察反馈后可调整 |
| 适合简单问答 | 适合复杂多步任务 |
