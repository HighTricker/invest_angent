# Invest Agent - 投资分析智能体

## 项目概述

一个投资训练追踪系统。用户通过前端界面录入投资标的和金额，系统每月自动获取价格、计算收益、发送邮件报告。面向初期投资者，强调月频纪律性查看，不做日频推送。

## 当前进度

### 已完成（Phase 1 核心功能全部完成）
- [x] 数据库设计（4张表：assets, monthly_prices, positions, position_changes）
- [x] 价格采集服务（yfinance + akshare，覆盖11个标的）
- [x] 数据分析服务（累计/月度涨跌幅、仓位价值、组合汇总）
- [x] 数据采集入库（collector.py，连接价格获取与数据库）
- [x] Streamlit 前端面板（代码/样式/文案三层分离）
- [x] 邮件报告发送（163 SMTP SSL 端口465，已验证）
- [x] 定时任务串联（run_monthly.py）
- [x] 11个标的已录入，每个 $1 初始仓位，2025-12 ~ 2026-02 历史数据已采集
- [x] 一键启动 bat 脚本（启动面板.bat）
- [x] 侧边栏一键发送邮件按钮

### 待开发（后期扩展）
- [ ] 部署到云服务器 + cron 定时任务
- [ ] 投资资讯推送
- [ ] 投资思维训练模块
- [ ] 前端迁移：Streamlit → Flask + React（Phase 2）

## 技术栈

- **语言**: Python 3.11+
- **前端**: Streamlit（Phase 1）→ Flask + React（Phase 2）
- **数据存储**: SQLite（data/invest.db，已被 .gitignore 忽略）
- **数据获取**: yfinance（美股/港股/加密货币/美国国债）+ akshare（AU9999黄金/中国国债）
- **邮件**: SMTP SSL（163邮箱，端口465，配置在 .env）
- **定时任务**: cron（云服务器部署时配置）
- **包管理**: pip + requirements.txt

### 架构原则（分层设计，便于后期迁移）
- **UI 层**：Streamlit 页面，可整体替换
- **业务逻辑层**：price_fetcher / analyzer / collector / email_sender，纯 Python 模块
- **数据层**：SQLite，通过 database.py 统一操作

## 投资标的列表（11个，每个 $1 初始仓位）

| 标的 | 代码 | 资产类别 | 基准价格（2025-12） | 数据源 |
|------|------|----------|---------------------|--------|
| Google | GOOGL | 美股 | 313 | yfinance |
| Amazon | AMZN | 美股 | 233.88 | yfinance |
| Facebook | META | 美股 | 640.87 | yfinance |
| Apple | AAPL | 美股 | 283.1 | yfinance |
| Tencent | 0700.HK | 港股 | 619.5 | yfinance |
| Alibaba | BABA | 中概 | 164.26 | yfinance |
| NVDA | NVDA | 美股 | 179.91 | yfinance |
| 国际版黄金 | AU9999 | 大宗商品 | 958.46 | akshare |
| 10年期美国国债 | ^TNX | 债券 | 4.0962 | yfinance |
| 10年期中国国债 | CN10Y | 债券 | 1.827 | akshare |
| 比特币 | BTC-USD | 加密货币 | 86309.1 | yfinance |

## 项目结构

```
invest_anget/
├── CLAUDE.md                      # 项目说明（本文件）
├── .env                           # SMTP 配置（不提交 Git）
├── .env.example                   # 配置模板
├── requirements.txt               # Python 依赖
├── run_monthly.py                 # 定时任务入口脚本
├── 启动面板.bat                    # 双击启动 Streamlit
├── 投资跟踪表格.xlsx               # 原始表格（参考用）
├── src/
│   ├── models/
│   │   └── database.py            # 数据库初始化与连接
│   ├── services/
│   │   ├── price_fetcher.py       # 价格数据采集（yfinance + akshare）
│   │   ├── collector.py           # 采集入库（价格获取→写入数据库）
│   │   ├── analyzer.py            # 数据分析与计算
│   │   ├── email_sender.py        # 邮件报告（HTML生成 + SMTP发送）
│   │   └── monthly_job.py         # 月度任务编排（采集→分析→邮件）
│   ├── agents/                    # Agent 逻辑（待开发）
│   └── utils/                     # 工具函数
├── frontend/
│   ├── app.py                     # 主入口（导航 + 样式加载 + 邮件按钮）
│   ├── pages/
│   │   ├── dashboard.py           # 投资总览（指标卡片、涨跌卡片、明细表格）
│   │   ├── manage.py              # 标的管理（添加标的、加仓减仓、数据采集）
│   │   └── history.py             # 仓位变动记录
│   ├── components/charts.py       # 图表组件
│   ├── styles/main.css            # 全部 CSS 样式
│   └── texts/zh_CN.py             # 全部中文文案
├── tests/                         # 测试代码
└── data/                          # 数据库文件（.db 被 .gitignore 忽略）
```

## 开发规范

### 代码风格
- 遵循 PEP 8，使用 type hints
- 注释和 docstring 用中文
- 变量/函数 snake_case，类 PascalCase

### 前端三层分离
- **改文字** → 编辑 `frontend/texts/zh_CN.py`
- **改样式** → 编辑 `frontend/styles/main.css`
- **改逻辑** → 编辑 `frontend/pages/*.py`

### 工作流程
- **稳健优先**：方案先确认再动手，代码先测试再提交
- 修改代码前先告知方案，获得用户同意后再执行
- 不做过度设计，只实现当前需要的功能

### Git 规范
- commit message 中文，格式：`<类型>: <描述>`
- 类型：feat / fix / refactor / docs / test / chore

### 启动方式
```bash
cd E:\invest_anget
set PYTHONPATH=E:\invest_anget
streamlit run frontend/app.py
```
或双击 `启动面板.bat`

## 沟通约定

- 始终使用中文交流
- 遇到不确定的技术选型时，先列出选项和利弊，等待确认后再行动
- 涉及 API key、密码等敏感信息时，使用环境变量，不硬编码
