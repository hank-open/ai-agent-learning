"""
Mock 数据库

真实项目里这些数据来自 MySQL / PostgreSQL / 商品搜索服务。
现在用 Python dict 模拟，让我们专注在 Agent 逻辑本身，而不是数据库。

数据结构和真实电商系统保持一致，以后替换成真实 DB 调用只需改工具层。
"""

# ── 订单表 ────────────────────────────────────────────────────────────
# key = order_id，value = 订单详情
ORDERS: dict[str, dict] = {
    "ORD-2024-001": {
        "order_id":    "ORD-2024-001",
        "user_id":     "U001",
        "product":     "蓝牙耳机 Pro",
        "quantity":    1,
        "price":       299.0,
        "status":      "shipped",          # pending / paid / shipped / delivered / cancelled
        "address":     "上海市浦东新区张江高科技园区 100 号",
        "created_at":  "2024-04-20",
        "tracking_no": "SF1234567890",     # 快递单号
    },
    "ORD-2024-002": {
        "order_id":    "ORD-2024-002",
        "user_id":     "U001",
        "product":     "手机壳（红色）",
        "quantity":    2,
        "price":       49.0,
        "status":      "delivered",
        "address":     "上海市浦东新区张江高科技园区 100 号",
        "created_at":  "2024-04-15",
        "tracking_no": "SF0987654321",
    },
    "ORD-2024-003": {
        "order_id":    "ORD-2024-003",
        "user_id":     "U002",
        "product":     "机械键盘",
        "quantity":    1,
        "price":       599.0,
        "status":      "pending",          # 还没付款
        "address":     "北京市朝阳区 CBD 88 号",
        "created_at":  "2024-04-27",
        "tracking_no": None,               # 未发货，没有快递单号
    },
}

# 订单状态的中文映射（用于生成用户友好的回复）
ORDER_STATUS_ZH: dict[str, str] = {
    "pending":   "待付款",
    "paid":      "已付款，等待发货",
    "shipped":   "已发货，运输中",
    "delivered": "已签收",
    "cancelled": "已取消",
}


# ── 商品表 ────────────────────────────────────────────────────────────
PRODUCTS: list[dict] = [
    {
        "product_id": "P001",
        "name":       "蓝牙耳机 Pro",
        "category":   "数码",
        "price":      299.0,
        "stock":      {"黑色": 50, "白色": 30, "蓝色": 0},   # 蓝色无货
        "rating":     4.8,
        "description": "主动降噪，续航 30 小时，IPX5 防水",
    },
    {
        "product_id": "P002",
        "name":       "手机壳",
        "category":   "配件",
        "price":      49.0,
        "stock":      {"红色": 100, "黑色": 80, "蓝色": 60, "透明": 200},
        "rating":     4.5,
        "description": "全包边防摔，支持无线充电",
    },
    {
        "product_id": "P003",
        "name":       "机械键盘",
        "category":   "数码",
        "price":      599.0,
        "stock":      {"黑色": 20, "白色": 15},
        "rating":     4.9,
        "description": "Cherry MX 红轴，RGB 背光，铝合金外壳",
    },
    {
        "product_id": "P004",
        "name":       "无线鼠标",
        "category":   "数码",
        "price":      159.0,
        "stock":      {"黑色": 45, "白色": 30},
        "rating":     4.6,
        "description": "2.4G 无线，续航 12 个月，DPI 可调",
    },
    {
        "product_id": "P005",
        "name":       "手机壳（透明）",   # 故意加一个相似商品，测试搜索精度
        "category":   "配件",
        "price":      29.0,
        "stock":      {"透明": 500},
        "rating":     4.2,
        "description": "超薄 0.3mm，不发黄材质",
    },
]


# ── 退换货政策 ─────────────────────────────────────────────────────────
# 真实系统里这些来自 CMS 或文档库，通过 RAG 检索
POLICIES: list[dict] = [
    {
        "policy_id": "POL-001",
        "title":     "退货政策",
        "content":   (
            "所有商品支持 7 天无理由退货。"
            "商品需保持原包装，未使用状态。"
            "退货运费由买家承担（商品质量问题除外）。"
            "退款将在收到商品后 3 个工作日内原路退回。"
        ),
    },
    {
        "policy_id": "POL-002",
        "title":     "换货政策",
        "content":   (
            "商品质量问题支持 30 天换货。"
            "换货运费由卖家承担。"
            "非质量问题换货，运费由买家承担。"
        ),
    },
    {
        "policy_id": "POL-003",
        "title":     "发货时效",
        "content":   (
            "付款后 24 小时内发货（节假日顺延）。"
            "默认顺丰快递，一般 1-3 个工作日到达。"
            "偏远地区可能需要 3-7 个工作日。"
        ),
    },
]
