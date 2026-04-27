"""
商品相关工具

搜索工具是 Agent 系统里最容易出问题的地方：
  - 召回不全：用户说"耳机"，没搜到"蓝牙耳机 Pro"
  - 召回太多：返回 50 条结果，Agent 处理不了
  - 相关性差：搜"手机壳蓝色"，排第一的是不相关商品

本文件演示两种搜索策略并说明差异。
后续模块 7（工具调用优化）会深入处理这些问题。
"""

from ..data.mock_data import PRODUCTS


def search_products(query: str, top_k: int = 3) -> str:
    """
    商品搜索。

    当前实现：关键词匹配（简单但有效）
    后续升级：向量语义搜索（处理"便宜耳机"→ 匹配"蓝牙耳机 Pro"）

    Args:
        query:  搜索词，如 "蓝色手机壳" 或 "降噪耳机"
        top_k:  返回最多几条结果

    Returns:
        str: 商品列表描述
    """
    query_lower = query.lower()

    # 给每个商品打分
    # 这是一个非常简单的相关性打分，生产里用 BM25 或向量相似度
    scored = []
    for product in PRODUCTS:
        score = 0

        # 商品名匹配：权重最高
        # 用户说"手机壳"，商品名包含"手机壳"就加分
        name_lower = product["name"].lower()
        for word in query_lower.split():            # 按空格分词（简单分词）
            if word in name_lower:
                score += 3                           # 名称匹配权重 3

        # 品类匹配：权重中等
        category_lower = product["category"].lower()
        if any(w in category_lower for w in query_lower.split()):
            score += 2

        # 描述匹配：权重最低
        desc_lower = product["description"].lower()
        for word in query_lower.split():
            if word in desc_lower:
                score += 1

        # score > 0 才纳入结果（至少要有一个地方匹配）
        if score > 0:
            scored.append((score, product))

    if not scored:
        return f"未找到与「{query}」相关的商品。"

    # 按分数降序排列
    scored.sort(key=lambda x: -x[0])

    # 取 top_k
    results = [p for _, p in scored[:top_k]]

    # 格式化输出
    lines = [f"搜索「{query}」，找到 {len(results)} 件商品："]
    for p in results:
        # 把库存 dict 转成"黑色:50件 白色:30件"的形式
        stock_str = "  ".join(
            f"{color}:{qty}件" for color, qty in p["stock"].items()
        )
        lines.append(
            f"\n  [{p['product_id']}] {p['name']}\n"
            f"  价格：¥{p['price']}  评分：{p['rating']}\n"
            f"  库存：{stock_str}\n"
            f"  简介：{p['description']}"
        )

    return "\n".join(lines)


def check_stock(product_name: str, color: str = "") -> str:
    """
    查询特定商品的库存/颜色。

    和 search_products 的区别：
      search_products → 模糊搜索，返回多个匹配商品
      check_stock     → 精确查某商品的某颜色库存

    Args:
        product_name: 商品名（可以是关键词）
        color:        颜色（可选，不传则返回所有颜色库存）

    Returns:
        str: 库存信息描述
    """
    name_lower = product_name.lower()

    # 在商品库里找最匹配的一个商品
    # 注意这里只取第一个匹配，所以商品名尽量精确
    matched = next(
        (p for p in PRODUCTS if name_lower in p["name"].lower()),
        None
    )

    if not matched:
        return f"未找到商品「{product_name}」，请确认商品名称。"

    # 如果没有指定颜色，返回所有颜色的库存
    if not color:
        stock_lines = []
        for c, qty in matched["stock"].items():
            status = "有货" if qty > 0 else "暂时缺货"
            stock_lines.append(f"  {c}：{qty} 件（{status}）")
        return (
            f"「{matched['name']}」库存情况：\n"
            + "\n".join(stock_lines)
        )

    # 如果指定了颜色，精确查询
    color_lower = color.lower()

    # 遍历库存 dict 查找颜色
    # 用 lower() 做大小写无关匹配，用 in 允许部分匹配（"蓝" 匹配 "深蓝色"）
    for stock_color, qty in matched["stock"].items():
        if color_lower in stock_color.lower():
            if qty > 0:
                return f"「{matched['name']}」{stock_color}：库存 {qty} 件，可以下单。"
            else:
                return f"「{matched['name']}」{stock_color}：暂时缺货，预计 3-5 天补货。"

    # 颜色不存在于库存 dict 里
    available_colors = "、".join(matched["stock"].keys())
    return (
        f"「{matched['name']}」暂时没有{color}色，"
        f"目前有：{available_colors}。"
    )


def get_policy(topic: str) -> str:
    """
    查询退换货/发货政策。

    简单关键词匹配。真实系统里用 RAG（向量检索 + 重排）。
    模块 7 会详细讲如何优化检索质量。

    Args:
        topic: 查询主题，如 "退货" "换货" "发货"

    Returns:
        str: 相关政策内容
    """
    from ..data.mock_data import POLICIES

    topic_lower = topic.lower()

    # 找所有标题或内容包含关键词的政策
    matched = [
        p for p in POLICIES
        if topic_lower in p["title"].lower() or topic_lower in p["content"].lower()
    ]

    if not matched:
        return f"未找到关于「{topic}」的政策说明，请联系人工客服。"

    lines = []
    for p in matched:
        lines.append(f"【{p['title']}】\n{p['content']}")

    return "\n\n".join(lines)
