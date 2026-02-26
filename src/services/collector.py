"""
数据采集入库模块。

负责将 price_fetcher 获取到的价格写入数据库。
是连接"价格获取"和"数据存储"的桥梁。
既可被定时任务调用（自动采集），也可被前端按钮调用（手动采集）。
"""

from datetime import datetime
from typing import Optional

from src.models.database import get_connection
from src.services.price_fetcher import fetch_price


def collect_single(
    asset_id: int,
    target_date: str,
    db_path: str | None = None,
) -> Optional[float]:
    """
    采集单个标的指定日期的价格并写入数据库。

    如果该标的在该日期已有记录，则跳过不覆盖。

    Args:
        asset_id: 标的 ID。
        target_date: 目标日期，格式 "YYYY-MM-DD"。
        db_path: 数据库路径。

    Returns:
        写入的价格（float），跳过或失败时返回 None。
    """
    conn = get_connection(db_path)
    try:
        # 获取标的信息
        asset = conn.execute(
            "SELECT ticker, name FROM assets WHERE id = ? AND is_active = 1",
            (asset_id,)
        ).fetchone()
        if asset is None:
            return None

        # 检查是否已有记录（避免重复写入）
        existing = conn.execute(
            "SELECT id FROM monthly_prices WHERE asset_id = ? AND record_date = ?",
            (asset_id, target_date)
        ).fetchone()
        if existing:
            print(f"  [{asset['name']}] {target_date} 已有记录，跳过")
            return None

        # 调用 price_fetcher 获取价格
        price = fetch_price(asset["ticker"], target_date)
        if price is None:
            print(f"  [{asset['name']}] 价格获取失败")
            return None

        # 写入数据库
        conn.execute(
            "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
            "VALUES (?, ?, ?)",
            (asset_id, target_date, price),
        )
        conn.commit()
        print(f"  [{asset['name']}] {target_date} -> {price:.4f} (已入库)")
        return price
    finally:
        conn.close()


def collect_all(
    target_date: str,
    db_path: str | None = None,
) -> dict[str, Optional[float]]:
    """
    采集所有活跃标的在指定日期的价格并写入数据库。

    Args:
        target_date: 目标日期，格式 "YYYY-MM-DD"。
        db_path: 数据库路径。

    Returns:
        字典，key 为标的名称，value 为写入的价格或 None。
    """
    conn = get_connection(db_path)
    try:
        assets = conn.execute(
            "SELECT id, name FROM assets WHERE is_active = 1 ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    print(f"开始采集 {target_date} 的价格数据（共 {len(assets)} 个标的）...")
    results = {}
    for asset in assets:
        price = collect_single(asset["id"], target_date, db_path)
        results[asset["name"]] = price

    success = sum(1 for v in results.values() if v is not None)
    print(f"采集完成：{success}/{len(results)} 成功")
    return results


def collect_history(
    dates: list[str],
    db_path: str | None = None,
) -> None:
    """
    批量补录多个月份的历史价格数据。

    遍历每个日期，对所有活跃标的执行采集入库。
    已有记录的会自动跳过。

    Args:
        dates: 日期列表，格式 ["YYYY-MM-DD", ...]。
        db_path: 数据库路径。
    """
    for date in dates:
        print(f"\n=== 采集 {date} ===")
        collect_all(date, db_path)
