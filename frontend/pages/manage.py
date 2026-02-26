"""
标的管理页面。

支持添加新标的、设置投资金额（加仓/减仓）、查看当前持仓、手动采集价格。
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from frontend.texts import zh_CN as T
from src.models.database import get_connection
from src.services.collector import collect_all


def render(db_path: str | None = None) -> None:
    """渲染标的管理页面。"""
    st.header(T.MANAGE_TITLE)

    _render_add_asset(db_path)
    st.markdown("---")
    _render_invest(db_path)
    st.markdown("---")
    _render_collect(db_path)
    st.markdown("---")
    _render_positions(db_path)


def _render_add_asset(db_path: str | None) -> None:
    """渲染「添加新标的」区域。"""
    st.subheader(T.ADD_SECTION)

    with st.form("add_asset_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input(T.ADD_NAME, placeholder=T.ADD_NAME_PLACEHOLDER)
            ticker = st.text_input(T.ADD_TICKER, placeholder=T.ADD_TICKER_PLACEHOLDER)
        with col2:
            asset_type = st.selectbox(T.ADD_TYPE, T.ADD_TYPE_OPTIONS)
            base_price = st.number_input(T.ADD_BASE_PRICE, min_value=0.0, format="%.4f")

        base_date = st.date_input(T.ADD_BASE_DATE, value=date(2025, 12, 1))
        submitted = st.form_submit_button(T.ADD_BUTTON)

    if submitted:
        # 校验必填项
        if not name.strip() or not ticker.strip() or base_price <= 0:
            st.error(T.ADD_ERROR_EMPTY)
            return

        conn = get_connection(db_path)
        try:
            # 检查重复
            exists = conn.execute(
                "SELECT id FROM assets WHERE ticker = ?", (ticker.strip().upper(),)
            ).fetchone()
            if exists:
                st.error(T.ADD_ERROR_DUPLICATE.format(ticker=ticker.strip().upper()))
                return

            # 插入标的
            conn.execute(
                "INSERT INTO assets (name, ticker, asset_type, base_price, base_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (name.strip(), ticker.strip().upper(), asset_type, base_price,
                 base_date.strftime("%Y-%m-%d")),
            )
            conn.commit()
            st.success(T.ADD_SUCCESS.format(name=name.strip()))
        finally:
            conn.close()


def _render_invest(db_path: str | None) -> None:
    """渲染「设置投资金额」区域（加仓/减仓）。"""
    st.subheader(T.INVEST_SECTION)

    conn = get_connection(db_path)
    try:
        assets = conn.execute(
            "SELECT id, name, ticker FROM assets WHERE is_active = 1 ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    if not assets:
        st.info(T.DASHBOARD_NO_ASSETS)
        return

    # 标的选择
    asset_options = {f"{a['name']} ({a['ticker']})": a["id"] for a in assets}
    selected_label = st.selectbox(T.INVEST_SELECT_ASSET, list(asset_options.keys()))
    selected_id = asset_options[selected_label]

    # 显示当前持仓
    conn = get_connection(db_path)
    try:
        position = conn.execute(
            "SELECT total_invested FROM positions WHERE asset_id = ?",
            (selected_id,)
        ).fetchone()
    finally:
        conn.close()
    current_invested = position["total_invested"] if position else 0.0
    st.caption(f"当前持仓：${current_invested:,.2f}")

    # 金额输入
    amount = st.number_input(T.INVEST_AMOUNT, min_value=0.0, step=1.0, format="%.2f")
    note = st.text_input(T.INVEST_NOTE, placeholder=T.INVEST_NOTE_PLACEHOLDER)

    col1, col2 = st.columns(2)
    with col1:
        add_clicked = st.button(T.INVEST_BUTTON_ADD, use_container_width=True)
    with col2:
        reduce_clicked = st.button(T.INVEST_BUTTON_REDUCE, use_container_width=True)

    if add_clicked:
        if amount <= 0:
            st.error(T.INVEST_ERROR_ZERO)
            return
        _update_position(selected_id, amount, "加仓", note, db_path)
        asset_name = selected_label.split(" (")[0]
        st.success(T.INVEST_SUCCESS_ADD.format(name=asset_name, amount=amount))

    if reduce_clicked:
        if amount <= 0:
            st.error(T.INVEST_ERROR_ZERO)
            return
        if amount > current_invested:
            st.error(T.INVEST_ERROR_EXCEED.format(current=current_invested))
            return
        _update_position(selected_id, amount, "减仓", note, db_path)
        asset_name = selected_label.split(" (")[0]
        st.success(T.INVEST_SUCCESS_REDUCE.format(name=asset_name, amount=amount))


def _update_position(
    asset_id: int, amount: float, change_type: str, note: str,
    db_path: str | None,
) -> None:
    """
    更新持仓并记录变动日志。

    Args:
        asset_id: 标的 ID。
        amount: 变动金额（正数）。
        change_type: "加仓" 或 "减仓"。
        note: 备注。
        db_path: 数据库路径。
    """
    conn = get_connection(db_path)
    try:
        # 计算新的持仓金额
        position = conn.execute(
            "SELECT total_invested FROM positions WHERE asset_id = ?",
            (asset_id,)
        ).fetchone()

        if position is None:
            # 首次建仓
            new_total = amount if change_type == "加仓" else 0.0
            conn.execute(
                "INSERT INTO positions (asset_id, total_invested) VALUES (?, ?)",
                (asset_id, new_total),
            )
        else:
            current = position["total_invested"]
            new_total = current + amount if change_type == "加仓" else current - amount
            conn.execute(
                "UPDATE positions SET total_invested = ?, updated_at = datetime('now') "
                "WHERE asset_id = ?",
                (new_total, asset_id),
            )

        # 记录变动日志
        conn.execute(
            "INSERT INTO position_changes (asset_id, change_type, amount, change_date, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (asset_id, change_type, amount,
             datetime.now().strftime("%Y-%m-%d"), note or None),
        )
        conn.commit()
    finally:
        conn.close()


def _render_collect(db_path: str | None) -> None:
    """渲染「数据采集」区域，支持手动选择月份并采集价格。"""
    st.subheader(T.COLLECT_SECTION)

    conn = get_connection(db_path)
    try:
        asset_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM assets WHERE is_active = 1"
        ).fetchone()["cnt"]
    finally:
        conn.close()

    if asset_count == 0:
        st.info(T.COLLECT_NO_ASSETS)
        return

    # 生成可选月份列表：从 2025-12 到当前月份
    today = date.today()
    months = []
    year, month = 2025, 12
    while (year, month) <= (today.year, today.month):
        months.append(f"{year}-{month:02d}-01")
        month += 1
        if month > 12:
            month = 1
            year += 1

    selected_dates = st.multiselect(
        T.COLLECT_SELECT_DATES,
        options=months,
        default=[months[-1]] if months else [],
    )

    if st.button(T.COLLECT_BUTTON, use_container_width=True):
        if not selected_dates:
            return

        with st.spinner(T.COLLECT_RUNNING):
            total_success = 0
            total_skip = 0
            for d in sorted(selected_dates):
                results = collect_all(d, db_path)
                success = sum(1 for v in results.values() if v is not None)
                total_success += success
                total_skip += len(results) - success

        st.success(T.COLLECT_SUCCESS.format(success=total_success, skip=total_skip))


def _render_positions(db_path: str | None) -> None:
    """渲染「当前持仓一览」表格。"""
    st.subheader(T.POSITION_SECTION)

    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT a.name, a.ticker, COALESCE(p.total_invested, 0) as invested "
            "FROM assets a "
            "LEFT JOIN positions p ON a.id = p.asset_id "
            "WHERE a.is_active = 1 "
            "ORDER BY a.id"
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        st.info(T.DASHBOARD_NO_ASSETS)
        return

    data = [{
        T.POSITION_COL_NAME: r["name"],
        T.POSITION_COL_TICKER: r["ticker"],
        T.POSITION_COL_INVESTED: f"${r['invested']:,.2f}",
    } for r in rows]

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
