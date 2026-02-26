"""
Invest Agent 前端主入口。

负责：
1. 加载自定义 CSS 样式
2. 初始化数据库
3. 侧边栏导航
4. 路由到对应页面
"""

import streamlit as st
from pathlib import Path

from frontend.texts import zh_CN as T
from frontend.pages import dashboard, manage, history
from src.models.database import init_db, get_connection
from src.services.analyzer import analyze_portfolio
from src.services.email_sender import send_monthly_report

# ---- 页面配置 ----
st.set_page_config(
    page_title=T.APP_TITLE,
    page_icon=T.APP_ICON,
    layout="wide",
)

# ---- 加载自定义样式 ----
css_path = Path(__file__).parent / "styles" / "main.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

# ---- 初始化数据库 ----
init_db()

# ---- 侧边栏导航 ----
st.sidebar.title(T.APP_TITLE)
page = st.sidebar.radio(
    "导航",
    [T.NAV_DASHBOARD, T.NAV_MANAGE, T.NAV_HISTORY],
    label_visibility="collapsed",
)

# ---- 侧边栏：邮件报告 ----
st.sidebar.markdown("---")
st.sidebar.subheader(T.SIDEBAR_EMAIL_SECTION)

# 获取可用月份
conn = get_connection()
_dates = conn.execute(
    "SELECT DISTINCT record_date FROM monthly_prices ORDER BY record_date"
).fetchall()
conn.close()
_date_list = [row["record_date"] for row in _dates]

if _date_list:
    _selected = st.sidebar.selectbox(
        "报告月份", _date_list, index=len(_date_list) - 1, key="email_date"
    )
    if st.sidebar.button(T.SIDEBAR_EMAIL_BUTTON, use_container_width=True):
        with st.sidebar:
            with st.spinner(T.SIDEBAR_EMAIL_SENDING):
                summary = analyze_portfolio(_selected)
                if summary.asset_analyses:
                    result = send_monthly_report(summary, _selected)
                    if result:
                        st.success(T.SIDEBAR_EMAIL_SUCCESS)
                    else:
                        st.error(T.SIDEBAR_EMAIL_FAIL)
                else:
                    st.warning(T.SIDEBAR_EMAIL_NO_DATA)
else:
    st.sidebar.info(T.SIDEBAR_EMAIL_NO_DATA)

# ---- 路由 ----
if page == T.NAV_DASHBOARD:
    dashboard.render()
elif page == T.NAV_MANAGE:
    manage.render()
elif page == T.NAV_HISTORY:
    history.render()
