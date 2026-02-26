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
from src.models.database import init_db

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

# ---- 路由 ----
if page == T.NAV_DASHBOARD:
    dashboard.render()
elif page == T.NAV_MANAGE:
    manage.render()
elif page == T.NAV_HISTORY:
    history.render()
