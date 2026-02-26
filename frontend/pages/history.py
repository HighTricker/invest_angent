"""
仓位变动记录页面。

按时间倒序展示所有加仓/减仓操作日志，便于追溯资金变动历史。
"""

import streamlit as st
import pandas as pd

from frontend.texts import zh_CN as T
from src.models.database import get_connection


def render(db_path: str | None = None) -> None:
    """渲染变动记录页面。"""
    st.header(T.HISTORY_TITLE)

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT pc.change_date, a.name, a.ticker, "
            "pc.change_type, pc.amount, pc.price_at_change, pc.note "
            "FROM position_changes pc "
            "JOIN assets a ON pc.asset_id = a.id "
            "ORDER BY pc.change_date DESC, pc.created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        st.info(T.HISTORY_EMPTY)
        return

    data = []
    for r in rows:
        price_str = f"${r['price_at_change']:,.4f}" if r["price_at_change"] else "-"
        data.append({
            T.HISTORY_COL_DATE: r["change_date"],
            T.HISTORY_COL_ASSET: f"{r['name']} ({r['ticker']})",
            T.HISTORY_COL_TYPE: r["change_type"],
            T.HISTORY_COL_AMOUNT: f"${r['amount']:,.2f}",
            T.HISTORY_COL_PRICE: price_str,
            T.HISTORY_COL_NOTE: r["note"] or "",
        })

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
