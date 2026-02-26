# Invest Agent - 投资训练追踪系统

灵感来自李笑来《财富自由之路》中的投资训练想法，在此感谢李笑来先生。

这个项目帮助你做投资模拟练习：录入你感兴趣的投资标的，每月自动采集收盘价，计算收益表现，并通过邮件发送月度报告。强调**月频纪律性查看**，不做日频推送，培养长期投资思维。

## 功能

- **投资总览** — 组合总价值、总收益率、各标的涨跌卡片（涨绿跌红）、明细表格
- **标的管理** — 添加新标的、加仓/减仓、手动采集价格数据
- **仓位历史** — 查看所有仓位变动记录
- **邮件报告** — 一键发送月度投资报告到邮箱，移动端适配
- **定时任务** — 支持 cron 配置，每月 2 日自动采集上月收盘价并发送报告

## 支持的资产类型

美股、港股、中概股、加密货币、黄金（AU9999）、美国国债、中国国债

数据源：[yfinance](https://github.com/ranaroussi/yfinance) + [akshare](https://github.com/akfamily/akshare)

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/HighTricker/invest_angent.git
cd invest_angent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置邮箱（可选）

如需使用邮件报告功能，复制环境变量模板并填入你的 SMTP 配置：

```bash
cp .env.example .env
```

编辑 `.env`，填入你的邮箱和授权码（支持 163 / Gmail / QQ 邮箱）。

### 4. 启动

```bash
streamlit run frontend/app.py
```

Windows 用户也可以双击 `启动面板.bat` 一键启动。

## 技术栈

- **语言**: Python 3.11+
- **前端**: Streamlit
- **数据库**: SQLite
- **数据获取**: yfinance + akshare
- **邮件**: SMTP SSL

## 项目结构

```
invest_angent/
├── frontend/          # Streamlit 前端（页面、组件、样式、文案）
├── src/
│   ├── models/        # 数据库
│   └── services/      # 价格采集、数据分析、邮件发送、定时任务
├── run_monthly.py     # 定时任务入口
├── requirements.txt   # Python 依赖
└── .env.example       # 邮箱配置模板
```

---

<details>
<summary>English</summary>

Inspired by the investment training ideas in Li Xiaolai's book *The Road to Wealth Freedom*.

This project helps you practice investing: add the assets you're interested in, and the system automatically collects closing prices each month, calculates performance, and sends a monthly report to your email. It emphasizes **monthly disciplined review** rather than daily tracking, to build long-term investment thinking.

### Features

- Portfolio overview with gain/loss cards
- Asset management (add, increase/decrease positions)
- Position change history
- One-click monthly email report (mobile-friendly)
- Cron support for automated monthly data collection

### Quick Start

```bash
git clone https://github.com/HighTricker/invest_angent.git
cd invest_angent
pip install -r requirements.txt
cp .env.example .env  # Configure SMTP for email reports (optional)
streamlit run frontend/app.py
```

</details>
