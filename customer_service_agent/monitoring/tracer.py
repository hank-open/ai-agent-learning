"""
调用链追踪模块

追踪每一轮对话的：
  - 耗时（意图识别 / 工具调用 / LLM 生成 / 总计）
  - Token 消耗（来自 Anthropic API 响应头）
  - 路由决策
  - 意图识别结果

设计原则：
  - 非侵入式：Agent 主流程只需调用 tracer.start_turn() / tracer.end_turn()
  - 低开销：追踪本身不能影响主流程的延迟
  - 生产就绪：输出 JSON 方便接入 ELK / Datadog

用法：
    tracer = Tracer()
    tracer.start_turn()
    # ... 执行意图识别、工具调用、LLM 生成 ...
    tracer.record_intent(intent_result, elapsed_ms)
    tracer.record_tool(tool_name, elapsed_ms)
    tracer.record_llm(input_tokens, output_tokens, elapsed_ms)
    turn = tracer.end_turn(user_message, reply, routing_action)
    tracer.print_summary(turn)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TurnTrace:
    """单轮对话的完整追踪数据"""
    turn_id:        int
    user_message:   str
    reply:          str

    # 意图识别
    intent:         str   = ""
    confidence:     float = 0.0
    intent_ms:      float = 0.0

    # 工具调用（可能有 0 或多次）
    tools_called:   list[str]  = field(default_factory=list)
    tool_ms:        float      = 0.0

    # LLM 生成
    input_tokens:   int   = 0
    output_tokens:  int   = 0
    llm_ms:         float = 0.0

    # 路由决策
    routing_action: str   = ""

    # 总耗时
    total_ms:       float = 0.0

    def to_dict(self) -> dict:
        return {
            "turn_id":        self.turn_id,
            "user_message":   self.user_message[:80],
            "intent":         self.intent,
            "confidence":     round(self.confidence, 3),
            "routing":        self.routing_action,
            "tools":          self.tools_called,
            "tokens":         {"in": self.input_tokens, "out": self.output_tokens},
            "latency_ms":     {
                "intent": round(self.intent_ms),
                "tool":   round(self.tool_ms),
                "llm":    round(self.llm_ms),
                "total":  round(self.total_ms),
            },
        }


class Tracer:
    """
    调用链追踪器。每个 CustomerServiceAgent 实例持有一个 Tracer。
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._turn_count = 0
        self._turn_start: float = 0.0
        self._current: Optional[TurnTrace] = None
        self.history: list[TurnTrace] = []

    # ── 生命周期 ──────────────────────────────────────────────────────

    def start_turn(self) -> None:
        self._turn_count += 1
        self._turn_start = time.perf_counter()
        self._current = TurnTrace(
            turn_id=self._turn_count,
            user_message="",
            reply="",
        )

    def end_turn(
        self,
        user_message: str,
        reply: str,
        routing_action: str = "",
    ) -> TurnTrace:
        assert self._current is not None, "end_turn called before start_turn"
        t = self._current
        t.user_message   = user_message
        t.reply          = reply
        t.routing_action = routing_action
        t.total_ms       = (time.perf_counter() - self._turn_start) * 1000
        self.history.append(t)
        self._current = None

        if self.verbose:
            self.print_summary(t)

        return t

    # ── 记录各阶段指标 ────────────────────────────────────────────────

    def record_intent(self, intent: str, confidence: float, elapsed_ms: float) -> None:
        if self._current:
            self._current.intent     = intent
            self._current.confidence = confidence
            self._current.intent_ms  = elapsed_ms

    def record_tool(self, tool_name: str, elapsed_ms: float) -> None:
        if self._current:
            self._current.tools_called.append(tool_name)
            self._current.tool_ms += elapsed_ms

    def record_llm(self, input_tokens: int, output_tokens: int, elapsed_ms: float) -> None:
        if self._current:
            self._current.input_tokens  += input_tokens
            self._current.output_tokens += output_tokens
            self._current.llm_ms        += elapsed_ms

    # ── 输出 ──────────────────────────────────────────────────────────

    def print_summary(self, turn: TurnTrace) -> None:
        d = turn.to_dict()
        print(
            f"[trace #{d['turn_id']}] "
            f"intent={d['intent']} conf={d['confidence']} "
            f"routing={d['routing']} tools={d['tools']} "
            f"tokens={d['tokens']['in']}+{d['tokens']['out']} "
            f"latency={d['latency_ms']['total']}ms"
        )

    def dump_json(self) -> str:
        """导出所有追踪记录为 JSON 字符串（方便写入日志文件）"""
        return json.dumps([t.to_dict() for t in self.history], ensure_ascii=False, indent=2)

    def stats(self) -> dict:
        """汇总统计（用于评测或监控大盘）"""
        if not self.history:
            return {}
        total_tokens = sum(t.input_tokens + t.output_tokens for t in self.history)
        avg_latency  = sum(t.total_ms for t in self.history) / len(self.history)
        human_count  = sum(1 for t in self.history if t.routing_action == "human")
        return {
            "turns":           len(self.history),
            "total_tokens":    total_tokens,
            "avg_latency_ms":  round(avg_latency),
            "human_handoffs":  human_count,
        }
