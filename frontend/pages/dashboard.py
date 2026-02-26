"""
投资总览页面。

展示投资组合的关键指标、各标的涨跌卡片和明细表格。
"""

import streamlit as st
import pandas as pd

from frontend.texts import zh_CN as T
from src.models.database import get_connection
from src.services.analyzer import analyze_portfolio


def render(db_path: str | None = None) -> None:
    """渲染投资总览页面。"""
    st.header(T.DASHBOARD_TITLE)

    conn = get_connection(db_path)
    try:
        # 获取所有有价格数据的月份
        dates = conn.execute(
            "SELECT DISTINCT record_date FROM monthly_prices ORDER BY record_date"
        ).fetchall()
        date_list = [row["record_date"] for row in dates]

        # 检查是否有标的
        asset_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM assets WHERE is_active = 1"
        ).fetchone()["cnt"]
    finally:
        conn.close()

    if asset_count == 0:
        st.info(T.DASHBOARD_NO_ASSETS)
        return

    if not date_list:
        st.info(T.DASHBOARD_NO_DATA)
        return

    # 月份选择器
    selected_date = st.selectbox(
        T.DASHBOARD_SELECT_DATE,
        options=date_list,
        index=len(date_list) - 1,  # 默认选最新月份
    )

    # 分析组合
    summary = analyze_portfolio(selected_date, db_path)

    if not summary.asset_analyses:
        st.info(T.DASHBOARD_NO_DATA)
        return

    # ---- 关键指标卡片 ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(T.METRIC_TOTAL_INVESTED, f"${summary.total_invested:,.2f}")
    with col2:
        st.metric(T.METRIC_TOTAL_VALUE, f"${summary.total_current_value:,.2f}")
    with col3:
        st.metric(
            T.METRIC_TOTAL_RETURN,
            f"{summary.total_return:+.2%}",
        )
    with col4:
        st.metric(
            T.METRIC_PROFIT_LOSS,
            f"${summary.total_profit_loss:+,.2f}",
        )

    # ---- 最佳/最差 + 各标的涨跌卡片 ----
    # 完全采用邮件报告中的 HTML 卡片样式
    cards_html = '<div style="display:flex;flex-wrap:wrap;gap:12px;margin:8px 0">'

    # 最佳标的卡片
    if summary.best_performer and summary.best_performer.monthly_return is not None:
        b = summary.best_performer
        cards_html += (
            f'<div style="display:inline-block;background:#e8f5e9;padding:12px 20px;'
            f'border-radius:8px;text-align:center;min-width:160px;'
            f'flex:1 1 calc(25% - 12px)">'
            f'<div style="color:#666;font-size:13px">{T.BEST_PERFORMER}</div>'
            f'<div style="font-size:18px;font-weight:600">{b.name}</div>'
            f'<div style="color:#00c853;font-size:16px">{b.monthly_return:+.2%}</div>'
            f'</div>'
        )

    # 最差标的卡片
    if summary.worst_performer and summary.worst_performer.monthly_return is not None:
        w = summary.worst_performer
        cards_html += (
            f'<div style="display:inline-block;background:#ffebee;padding:12px 20px;'
            f'border-radius:8px;text-align:center;min-width:160px;'
            f'flex:1 1 calc(25% - 12px)">'
            f'<div style="color:#666;font-size:13px">{T.WORST_PERFORMER}</div>'
            f'<div style="font-size:18px;font-weight:600">{w.name}</div>'
            f'<div style="color:#ff1744;font-size:16px">{w.monthly_return:+.2%}</div>'
            f'</div>'
        )

    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("")

    # 各标的卡片
    cards_html = '<div style="display:flex;flex-wrap:wrap;gap:12px;margin:8px 0">'
    for a in summary.asset_analyses:
        ret = a.cumulative_return
        color = "#00c853" if ret >= 0 else "#ff1744"
        bg = "#e8f5e9" if ret >= 0 else "#ffebee"
        cards_html += (
            f'<div style="display:inline-block;background:{bg};padding:12px 20px;'
            f'border-radius:8px;text-align:center;min-width:160px;'
            f'flex:1 1 calc(25% - 12px)">'
            f'<div style="color:#666;font-size:13px">{a.asset_type}</div>'
            f'<div style="font-size:18px;font-weight:600">{a.name}</div>'
            f'<div style="color:{color};font-size:16px">{ret:+.2%}</div>'
            f'</div>'
        )
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

    st.markdown("---")

    # ---- 标的明细表格 ----
    st.subheader(T.TABLE_TITLE)

    rows = []
    for a in summary.asset_analyses:
        rows.append({
            T.TABLE_COL_NAME: a.name,
            T.TABLE_COL_TICKER: a.ticker,
            T.TABLE_COL_TYPE: a.asset_type,
            T.TABLE_COL_BASE_PRICE: f"{a.base_price:,.4f}",
            T.TABLE_COL_CURRENT_PRICE: f"{a.current_price:,.4f}",
            T.TABLE_COL_INVESTED: f"${a.total_invested:,.2f}",
            T.TABLE_COL_CURRENT_VALUE: f"${a.current_value:,.2f}",
            T.TABLE_COL_CUMULATIVE: f"{a.cumulative_return:+.2%}",
            T.TABLE_COL_MONTHLY: f"{a.monthly_return:+.2%}" if a.monthly_return is not None else "-",
            T.TABLE_COL_PROFIT_LOSS: f"${a.profit_loss:+,.2f}",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
