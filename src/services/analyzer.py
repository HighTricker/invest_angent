"""
数据分析与计算模块。

负责根据价格数据计算各类投资指标：
- 累计涨跌幅（相对初始买入价格）
- 月度涨跌幅（相对上月价格）
- 当前仓位价值
- 整体投资组合汇总
"""

from dataclasses import dataclass
from typing import Optional

import sqlite3
from src.models.database import get_connection


@dataclass
class AssetAnalysis:
    """单个标的的分析结果。"""
    asset_id: int               # 标的 ID
    name: str                   # 标的名称
    ticker: str                 # 交易代码
    asset_type: str             # 资产类别
    base_price: float           # 基准价格（初始买入价）
    current_price: float        # 当前价格（最新月度收盘价）
    previous_price: Optional[float]  # 上月价格（用于计算月度涨跌幅）
    total_invested: float       # 累计投入金额
    cumulative_return: float    # 累计涨跌幅（小数，如 0.08 表示 +8%）
    monthly_return: Optional[float]  # 月度涨跌幅（小数），首月为 None
    current_value: float        # 当前仓位价值 = 投入金额 × (1 + 累计涨跌幅)
    profit_loss: float          # 盈亏金额 = 当前价值 - 投入金额


@dataclass
class PortfolioSummary:
    """整体投资组合汇总。"""
    total_invested: float           # 总投入金额
    total_current_value: float      # 总当前价值
    total_profit_loss: float        # 总盈亏金额
    total_return: float             # 总收益率（加权）
    best_performer: Optional[AssetAnalysis]   # 本月表现最好的标的
    worst_performer: Optional[AssetAnalysis]  # 本月表现最差的标的
    asset_analyses: list[AssetAnalysis]       # 所有标的的分析明细


def analyze_asset(
    asset_id: int,
    target_date: str,
    db_path: str | None = None,
) -> Optional[AssetAnalysis]:
    """
    分析单个标的的投资表现。

    Args:
        asset_id: 标的 ID。
        target_date: 目标月份日期，格式 "YYYY-MM-DD"。
        db_path: 数据库路径，为 None 时使用默认路径。

    Returns:
        AssetAnalysis 对象，数据不足时返回 None。
    """
    conn = get_connection(db_path)
    try:
        # 1. 获取标的基本信息
        asset = conn.execute(
            "SELECT * FROM assets WHERE id = ? AND is_active = 1",
            (asset_id,)
        ).fetchone()
        if asset is None:
            return None

        # 2. 获取持仓金额
        position = conn.execute(
            "SELECT total_invested FROM positions WHERE asset_id = ?",
            (asset_id,)
        ).fetchone()
        total_invested = position["total_invested"] if position else 0.0

        # 3. 获取目标月份的收盘价（当前价格）
        current_record = conn.execute(
            "SELECT close_price FROM monthly_prices "
            "WHERE asset_id = ? AND record_date = ?",
            (asset_id, target_date)
        ).fetchone()
        if current_record is None:
            # 目标月份没有价格数据，无法分析
            return None
        current_price = current_record["close_price"]

        # 4. 获取上个月的收盘价（用于计算月度涨跌幅）
        previous_record = conn.execute(
            "SELECT close_price FROM monthly_prices "
            "WHERE asset_id = ? AND record_date < ? "
            "ORDER BY record_date DESC LIMIT 1",
            (asset_id, target_date)
        ).fetchone()
        previous_price = previous_record["close_price"] if previous_record else None

        # 5. 计算各项指标
        base_price = asset["base_price"]

        # 累计涨跌幅 = (当前价格 - 基准价格) / 基准价格
        cumulative_return = (current_price - base_price) / base_price

        # 月度涨跌幅 = (当前价格 - 上月价格) / 上月价格
        monthly_return = None
        if previous_price is not None:
            monthly_return = (current_price - previous_price) / previous_price

        # 当前仓位价值 = 投入金额 × (1 + 累计涨跌幅)
        current_value = total_invested * (1 + cumulative_return)

        # 盈亏金额
        profit_loss = current_value - total_invested

        return AssetAnalysis(
            asset_id=asset["id"],
            name=asset["name"],
            ticker=asset["ticker"],
            asset_type=asset["asset_type"],
            base_price=base_price,
            current_price=current_price,
            previous_price=previous_price,
            total_invested=total_invested,
            cumulative_return=cumulative_return,
            monthly_return=monthly_return,
            current_value=current_value,
            profit_loss=profit_loss,
        )
    finally:
        conn.close()


def analyze_portfolio(
    target_date: str,
    db_path: str | None = None,
) -> PortfolioSummary:
    """
    分析整体投资组合表现。

    遍历所有活跃标的，计算每个标的的分析指标，并汇总为组合层面的数据。

    Args:
        target_date: 目标月份日期，格式 "YYYY-MM-DD"。
        db_path: 数据库路径，为 None 时使用默认路径。

    Returns:
        PortfolioSummary 对象。
    """
    conn = get_connection(db_path)
    try:
        # 获取所有活跃标的
        assets = conn.execute(
            "SELECT id FROM assets WHERE is_active = 1"
        ).fetchall()
    finally:
        conn.close()

    # 逐个分析
    analyses: list[AssetAnalysis] = []
    for asset in assets:
        result = analyze_asset(asset["id"], target_date, db_path)
        if result is not None:
            analyses.append(result)

    # 汇总计算
    total_invested = sum(a.total_invested for a in analyses)
    total_current_value = sum(a.current_value for a in analyses)
    total_profit_loss = total_current_value - total_invested
    total_return = (total_profit_loss / total_invested) if total_invested > 0 else 0.0

    # 找出本月表现最好和最差的标的（基于月度涨跌幅）
    analyses_with_monthly = [a for a in analyses if a.monthly_return is not None]
    best = max(analyses_with_monthly, key=lambda a: a.monthly_return) if analyses_with_monthly else None
    worst = min(analyses_with_monthly, key=lambda a: a.monthly_return) if analyses_with_monthly else None

    return PortfolioSummary(
        total_invested=total_invested,
        total_current_value=total_current_value,
        total_profit_loss=total_profit_loss,
        total_return=total_return,
        best_performer=best,
        worst_performer=worst,
        asset_analyses=analyses,
    )
