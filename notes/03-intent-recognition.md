# 模块 1：意图识别（Intent Recognition）

## 为什么意图识别是 Agent 的入口

不做意图识别，直接把用户消息扔给 LLM 处理，在简单 demo 里没问题。但生产场景下会失控：

```
用户: "我上周买的那个红色手机壳，能退吗？还有你们有没有蓝色的？"

如果没有意图识别层：
  LLM 可能只处理退货，忽略库存查询
  LLM 可能把两件事混在一起回答
  无法路由到正确的处理模块
  无法知道缺少什么参数（订单号）

有了意图识别层：
  主意图: AFTER_SALES/return_request, slots={product_name: 手机壳}
  次意图: PRODUCT/check_stock, slots={product_name: 手机壳, color: 蓝色}
  缺失必填槽: order_id → 触发追问
```

---

## 三层架构

```
Layer 1: Domain（粗粒度域）
  ORDER / PRODUCT / AFTER_SALES / ACCOUNT / GENERAL
  作用：第一道分流，决定路由到哪个专家 Agent

Layer 2: Intent（细粒度意图）
  ORDER → query_order_status / cancel_order / modify_order / payment_issue
  作用：决定执行什么操作，调用什么工具

Layer 3: Slots（槽位参数）
  cancel_order → {order_id?, reason?}
  作用：执行操作所需的具体参数
        ? 表示 Optional，缺失时触发追问
```

为什么要分三层而不是一步到位？

- 粗粒度域识别准确率高（容易），可以先快速分流
- 细粒度意图在特定域内识别，上下文更聚焦，准确率更高
- 槽位提取和意图分开处理，逻辑更清晰，也更容易单独优化

---

## 关键工程决策：Structured Output

### 方案 A（脆弱，不要用）

```python
# 让 LLM 输出文本，再用正则解析
response = "意图: ORDER/cancel_order, 槽位: order_id=ORD-001"
intent = re.search(r"意图: (.+?),", response).group(1)  # 脆弱
```

**问题：** LLM 输出格式不稳定。换个模型、换个 prompt 版本，正则就全坏。

### 方案 B（生产可用，本项目使用）

```python
# 用 tool_use 强制 LLM 输出 JSON，Pydantic 验证
response = client.messages.create(
    tools=[INTENT_TOOL],           # 定义 JSON Schema
    tool_choice={"type": "auto"},  # 强制调用工具
    ...
)
# Claude 保证输出符合 schema 的 JSON
raw = response.content[0].input   # 直接是 dict，不用解析
result = IntentResult(**raw)       # Pydantic 验证类型
```

**优势：**
- JSON Schema 定义了合法的输出范围（枚举值、数值范围等）
- 解析失败可以携带 schema 重试，而不是盲目重试
- 模型升级不影响解析逻辑

### 方案 C（最高精度，有成本）

在 B 的基础上加 few-shot examples，对难区分的边界情况给出示范。

---

## 置信度（Confidence）的工程意义

置信度不只是一个浮点数，它是整个系统的决策旋钮。

```
confidence ≥ 0.8  → 直接路由处理
confidence 0.5–0.8 → 追问确认 or 给出最可能的理解让用户纠正
confidence < 0.5   → 转人工 or 开放性追问
```

**关键：LLM 必须被训练成"诚实评估置信度"**。

做法：在 few-shot 里明确给出低置信的例子：

```json
// 用户说"我想改一下" → 给低置信
{
  "intent": "modify_order",
  "confidence": 0.45,  // 正确示范：模糊就给低分
  "slots": {}
}
```

如果 few-shot 里全是高置信的例子，LLM 会学会永远输出高置信，追问逻辑就失效了。

---

## Few-shot 工程

### 静态 vs 动态

| | 静态 Few-shot | 动态 Few-shot |
|---|---|---|
| 实现 | 固定几条例子写死在 prompt | 根据当前输入检索最相似的 K 条 |
| 效果 | 基础准确率 | 更高准确率（例子更相关） |
| 成本 | 低（固定 token 数） | 稍高（需要向量检索） |
| 实现难度 | 低 | 需要向量库 |

本项目现在用静态 + 关键词加权选择，后续升级为向量检索。

### 样本选择原则

优先覆盖"难区分的边界"，而不是覆盖所有意图：

```
✅ 退款进度（refund_status） vs 退货申请（return_request）  ← 容易混淆
✅ 投诉（complaint） vs 退货（return_request）              ← 容易混淆
✅ 置信度低的例子（模糊表达）                               ← 必须有
✅ 多意图的例子                                             ← 必须有
❌ 每个意图各一条打全 ← 价值低，样本数多但覆盖边界少
```

---

## 槽位（Slot Filling）与追问策略

### 必填 vs 选填

```python
REQUIRED_SLOTS = {
    "cancel_order":   ["order_id"],     # 不知道订单号就无法取消
    "modify_order":   ["order_id"],
    "return_request": ["order_id"],
    "query_order_status": [],           # 可以列出近期订单，不强制要求
}
```

设计原则：**只有"没有就无法执行"的槽位才设为必填**。其余尽量宽容，能执行就执行。

### 追问策略

一次只追问一个槽位：

```
❌ 差体验: "请问您的订单号、退换原因、联系方式分别是什么？"
✅ 好体验: "请问您的订单号是多少？"
           → 用户回答后 → "请问退换原因是什么？"
```

---

## 指代消解（Coreference Resolution）

用户经常使用省略和指代：

```
轮1: "我上周买的蓝牙耳机有点问题"
轮2: "就退那个"   ← "那个" = 蓝牙耳机
```

解决方案：把最近 N 轮对话历史传入意图识别的上下文。

```python
messages = conversation_history[-12:]  # 最近 6 轮
messages.append({"role": "user", "content": current_message})
```

**注意：** 不要传太多历史。超过 6-8 轮后，LLM 注意力下降，反而引入噪音。历史压缩（Summary Memory）是后续模块的内容。

---

## 多意图处理

一句话包含多个意图时，不能只处理一个。

```python
class IntentResult(BaseModel):
    domain:   Domain
    intent:   str
    confidence: float
    slots:    dict
    secondary_intents: list[IntentResult]  # 次级意图列表
```

路由层的处理策略：

```
策略 A: 顺序处理
  先处理主意图 → 回复用户 → 再处理次意图
  优点: 简单，不容易出错
  缺点: 效率低

策略 B: 并行处理
  同时调用多个专家 Agent
  优点: 快
  缺点: 回复需要合并，逻辑复杂

策略 C: 只处理主意图，把次意图存入待办队列
  下一轮对话自动触发
  优点: 用户体验自然
```

本项目默认策略 A，后续可升级。

---

## 数据结构总览

```python
IntentResult(
    domain      = "AFTER_SALES",       # Layer 1
    intent      = "return_request",    # Layer 2
    confidence  = 0.88,                # 决策旋钮
    slots       = {                    # Layer 3
        "product_name": "手机壳",
        "purchase_time": "上周",
    },
    secondary_intents = [              # 多意图
        IntentResult(
            domain     = "PRODUCT",
            intent     = "check_stock",
            confidence = 0.85,
            slots      = {"product_name": "手机壳", "color": "蓝色"},
        )
    ],
    needs_clarification    = True,                          # 追问信号
    clarification_question = "请问您的订单号是多少？",       # 追问话术
)
```

---

## 常见问题与优化方向

### 准确率低

1. 检查 few-shot 是否覆盖了出错的边界情况
2. 换更强的模型（haiku → sonnet）做意图识别
3. 升级动态 few-shot（向量检索最相似的例子）
4. 对错误案例做分析：是意图错了，还是槽位提取错了？分开优化

### 置信度不准

1. few-shot 里必须有低置信的例子
2. 在 system prompt 里明确说"诚实评估，模糊就给低分"
3. 收集线上数据后，可以用 LLM-as-judge 重新标注置信度，做校准

### 槽位提取不全

1. 在 slot schema 里加更详细的 description
2. 加针对该槽位的 few-shot 例子
3. 考虑把槽位提取拆成独立的一步（意图 → 再做槽位提取），两步准确率通常高于一步

### 延伸：何时不需要显式意图识别

如果 Agent 只有 1-2 个工具，且用户意图单一，可以跳过意图识别层，直接 tool_use。

意图识别层的价值在于：
- 需要路由到不同专家/模块
- 需要追问缺失参数
- 需要基于置信度决定是否转人工
- 需要多意图并行处理
