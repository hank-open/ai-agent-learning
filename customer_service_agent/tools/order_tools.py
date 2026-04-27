"""
订单相关工具

工具层的设计原则：
  1. 每个函数只做一件事（单一职责）
  2. 返回值始终是 str —— Agent 读的是自然语言描述，不是 dict
  3. 工具内部处理所有错误，不向 Agent 抛异常
     原因：Agent 拿到异常信息没法处理，拿到"订单不存在"可以向用户解释

为什么返回 str 而不是 dict？
  Agent 最终要生成自然语言回复，直接给它 str 描述效率更高。
  如果你需要结构化数据做进一步处理（如计算退款金额），
  可以返回 dict，但大多数客服场景不需要。
"""

# 从 mock 数据库导入数据
# 真实项目里这里会是 DB 查询 / API 调用
from ..data.mock_data import ORDERS, ORDER_STATUS_ZH


def lookup_order(order_id: str) -> str:
    """
    查询订单详情。

    Args:
        order_id: 订单号，如 "ORD-2024-001"

    Returns:
        str: 订单信息的自然语言描述，或错误信息
    """
    # strip() 去掉用户可能带的多余空格
    # upper() 统一大写，避免 "ord-2024-001" 找不到 "ORD-2024-001"
    order_id = order_id.strip().upper()

    # 字典查找，O(1)
    order = ORDERS.get(order_id)

    # 找不到订单：返回友好的错误描述，而不是 None 或抛异常
    if not order:
        return f"未找到订单 {order_id}。请确认订单号是否正确，或者查询您的其他订单。"

    # ORDER_STATUS_ZH 把内部状态码转成用户友好的中文
    # .get(status, status) 的意思：找到就用中文，找不到就原样返回（防御性编程）
    status_zh = ORDER_STATUS_ZH.get(order["status"], order["status"])

    # 根据是否有快递单号，决定是否展示物流信息
    tracking_info = (
        f"快递单号：{order['tracking_no']}"
        if order["tracking_no"]
        else "暂无快递单号（可能尚未发货）"
    )

    # 用 f-string 拼装自然语言描述
    # 格式对 Agent 理解很重要，结构清晰比紧凑更好
    return (
        f"订单 {order_id} 详情：\n"
        f"  商品：{order['product']}  数量：{order['quantity']}\n"
        f"  金额：¥{order['price']}\n"
        f"  状态：{status_zh}\n"
        f"  收货地址：{order['address']}\n"
        f"  {tracking_info}\n"
        f"  下单时间：{order['created_at']}"
    )


def cancel_order(order_id: str, reason: str = "") -> str:
    """
    取消订单。

    注意：这里我们模拟"取消"逻辑但不真的修改 ORDERS dict，
    原因是 mock 数据是模块级变量，修改会影响其他测试。
    真实系统里会执行 UPDATE orders SET status='cancelled' WHERE id=?

    Args:
        order_id: 订单号
        reason:   取消原因（可选，用于记录）

    Returns:
        str: 操作结果描述
    """
    order_id = order_id.strip().upper()
    order = ORDERS.get(order_id)

    if not order:
        return f"未找到订单 {order_id}，无法取消。"

    # 业务规则：只有特定状态的订单可以取消
    # 这类规则不要放在 prompt 里让 LLM 判断，要在工具里硬编码
    # 原因：LLM 可能判断错，业务规则必须确定性执行
    cancellable_statuses = {"pending", "paid"}
    if order["status"] not in cancellable_statuses:
        status_zh = ORDER_STATUS_ZH.get(order["status"], order["status"])
        return (
            f"订单 {order_id} 当前状态为「{status_zh}」，无法取消。\n"
            f"如需退货，请申请退货流程。"
        )

    # 模拟执行取消（真实场景：DB 更新 + 触发退款）
    reason_note = f"取消原因：{reason}" if reason else "未填写取消原因"
    return (
        f"订单 {order_id}（{order['product']}）已成功取消。\n"
        f"{reason_note}\n"
        f"退款 ¥{order['price']} 将在 3 个工作日内原路退回。"
    )


def get_user_recent_orders(user_id: str = "U001", limit: int = 3) -> str:
    """
    获取用户近期订单列表。

    用途：当用户说"查我的订单"但没提供订单号时，
    返回近期订单让用户自己选，而不是报错。

    Args:
        user_id: 用户 ID（真实系统里从登录态获取）
        limit:   返回条数

    Returns:
        str: 近期订单的摘要列表
    """
    # 筛选该用户的订单
    # values() 返回所有订单，用列表推导过滤
    user_orders = [
        order for order in ORDERS.values()
        if order["user_id"] == user_id
    ]

    if not user_orders:
        return "您暂时没有订单记录。"

    # 按下单时间倒序（最新的在前）
    # key=lambda o: o["created_at"] 用创建时间排序
    # reverse=True 倒序
    user_orders.sort(key=lambda o: o["created_at"], reverse=True)

    # 只取前 limit 条
    recent = user_orders[:limit]

    # 拼装成列表格式，让用户一眼看清
    lines = [f"您的近期订单（最近 {len(recent)} 条）："]
    for o in recent:
        status_zh = ORDER_STATUS_ZH.get(o["status"], o["status"])
        lines.append(
            f"  • {o['order_id']}  {o['product']}  ¥{o['price']}  【{status_zh}】"
        )

    return "\n".join(lines)
