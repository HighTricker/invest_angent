"""
可复用的图表组件。

所有图表的绘制逻辑集中在此模块，页面代码只需调用即可。
"""

import streamlit as st
import pandas as pd

from frontend.texts import zh_CN as T


def render_cumulative_return_chart(
    asset_analyses: list,
    all_dates: list[str],
    db_path: str | None = None,
) -> None:
    """
    绘制各标的累计收益率对比折线图。

    Args:
        asset_analyses: 当前月份的 AssetAnalysis 列表（用于获取标的信息）。
        all_dates: 所有月份日期列表，格式 ["2026-01-01", "2026-02-01", ...]。
        db_path: 数据库路径。
    """
    from src.models.database import get_connection

    if not asset_analyses or not all_dates:
        return

    conn = get_connection(db_path)
    try:
        # 构建数据：每个标的在每个月的累计涨跌幅
        chart_data = {}
        for a in asset_analyses:
            returns = []
            for date in all_dates:
                record = conn.execute(
                    "SELECT close_price FROM monthly_prices "
                    "WHERE asset_id = ? AND record_date = ?",
                    (a.asset_id, date)
                ).fetchone()
                if record:
                    cum_ret = (record["close_price"] - a.base_price) / a.base_price * 100
                    returns.append(cum_ret)
                else:
                    returns.append(None)
            chart_data[a.name] = returns
    finally:
        conn.close()

    df = pd.DataFrame(chart_data, index=all_dates)
    df.index.name = T.CHART_X_LABEL

    st.subheader(T.CHART_TITLE)
    st.line_chart(df)


def render_allocation_pie(asset_analyses: list) -> None:
    """
    绘制资产配置占比饼图。

    Args:
        asset_analyses: AssetAnalysis 列表。
    """
    invested = [a.total_invested for a in asset_analyses if a.total_invested > 0]
    names = [a.name for a in asset_analyses if a.total_invested > 0]

    if not invested:
        return

    df = pd.DataFrame({"标的": names, "投入金额": invested})
    st.subheader("资产配置占比")
    st.bar_chart(df.set_index("标的"))
