"""
意图体系的 Schema 定义

设计原则：
- 用 Pydantic 强类型，LLM 输出能直接验证
- 意图分两层：Domain（粗粒度）→ Intent（细粒度）
- Slot 支持 Optional，缺失时触发追问
- confidence 字段用于 routing 决策
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ─── Layer 1: Domain（粗粒度）────────────────────────────────────────

class Domain(str, Enum):
    ORDER       = "ORDER"       # 订单相关
    PRODUCT     = "PRODUCT"     # 商品查询
    AFTER_SALES = "AFTER_SALES" # 退换货/售后
    ACCOUNT     = "ACCOUNT"     # 账户/会员
    GENERAL     = "GENERAL"     # 闲聊/无关/打招呼


# ─── Layer 2: 细粒度意图 ──────────────────────────────────────────────

class OrderIntent(str, Enum):
    QUERY_STATUS   = "query_order_status"  # 查询订单状态/物流
    CANCEL         = "cancel_order"         # 取消订单
    MODIFY         = "modify_order"         # 修改订单（地址/数量）
    PAYMENT_ISSUE  = "payment_issue"        # 付款问题

class ProductIntent(str, Enum):
    SEARCH         = "product_search"       # 搜索商品
    CHECK_STOCK    = "check_stock"          # 查询库存/颜色/型号
    COMPARE        = "compare_products"     # 比较商品
    RECOMMEND      = "recommend"            # 推荐

class AfterSalesIntent(str, Enum):
    RETURN         = "return_request"       # 退货
    EXCHANGE       = "exchange_request"     # 换货
    REFUND_STATUS  = "refund_status"        # 退款进度
    COMPLAINT      = "complaint"            # 投诉

class AccountIntent(str, Enum):
    POINTS_QUERY   = "points_query"         # 查积分
    MEMBERSHIP     = "membership_info"      # 会员信息
    COUPON         = "coupon_query"         # 优惠券

class GeneralIntent(str, Enum):
    GREETING       = "greeting"
    FAREWELL       = "farewell"
    UNCLEAR        = "unclear"              # 无法识别


# ─── Layer 3: Slots（参数）────────────────────────────────────────────
# 每个槽位都是 Optional —— 缺失时需要追问，而不是报错

class OrderSlots(BaseModel):
    order_id:     Optional[str]  = Field(None, description="订单号，如 ORD-2024-001")
    product_name: Optional[str]  = Field(None, description="商品名称")
    reason:       Optional[str]  = Field(None, description="取消/退换原因")
    new_address:  Optional[str]  = Field(None, description="修改后的收货地址")

class ProductSlots(BaseModel):
    product_name: Optional[str]  = Field(None, description="商品名称关键词")
    category:     Optional[str]  = Field(None, description="品类，如手机/衣服/食品")
    color:        Optional[str]  = Field(None, description="颜色")
    size:         Optional[str]  = Field(None, description="尺寸/型号")
    price_range:  Optional[str]  = Field(None, description="价格区间，如 100-200元")

class AfterSalesSlots(BaseModel):
    order_id:     Optional[str]  = Field(None, description="订单号")
    product_name: Optional[str]  = Field(None, description="商品名称")
    reason:       Optional[str]  = Field(None, description="退换原因")
    issue_desc:   Optional[str]  = Field(None, description="问题描述（投诉专用）")


# ─── 最终输出结构 ─────────────────────────────────────────────────────

class IntentResult(BaseModel):
    """
    意图识别的完整输出。

    注意 confidence：
    - ≥ 0.8 → 直接路由
    - 0.5–0.8 → 低置信，可能需要确认
    - < 0.5 → 需要追问或转人工
    """
    domain:      Domain          = Field(..., description="粗粒度域")
    intent:      str             = Field(..., description="细粒度意图枚举值")
    confidence:  float           = Field(..., ge=0.0, le=1.0, description="置信度 0-1")
    slots:       dict            = Field(default_factory=dict, description="提取的槽位值")

    # 多意图支持：用户一句话包含多个意图
    secondary_intents: list[IntentResult] = Field(
        default_factory=list,
        description="次级意图（多意图场景）"
    )

    # 给前端/路由使用的信号
    needs_clarification: bool    = Field(False, description="是否需要追问")
    clarification_question: Optional[str] = Field(None, description="追问的具体问题")

    class Config:
        # 允许 secondary_intents 中的 IntentResult 自引用
        arbitrary_types_allowed = True


# ─── 追问决策规则 ─────────────────────────────────────────────────────

REQUIRED_SLOTS: dict[str, list[str]] = {
    # 这些意图必须有对应槽位，否则需要追问
    OrderIntent.CANCEL:        ["order_id"],
    OrderIntent.MODIFY:        ["order_id"],
    OrderIntent.QUERY_STATUS:  [],           # order_id 缺失时可以列出近期订单
    AfterSalesIntent.RETURN:   ["order_id"],
    AfterSalesIntent.EXCHANGE: ["order_id"],
}

def get_missing_required_slots(intent: str, slots: dict) -> list[str]:
    """返回必填但缺失的槽位名称"""
    required = REQUIRED_SLOTS.get(intent, [])
    return [s for s in required if not slots.get(s)]
