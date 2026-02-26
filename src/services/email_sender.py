"""
邮件报告发送模块。

负责生成月度投资报告的 HTML 内容并通过 SMTP 发送。
邮箱配置通过环境变量读取，不硬编码任何敏感信息。
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from dotenv import load_dotenv

from src.services.analyzer import PortfolioSummary, AssetAnalysis


# 加载 .env 文件中的环境变量
load_dotenv()


def send_monthly_report(
    summary: PortfolioSummary,
    report_month: str,
) -> bool:
    """
    发送月度投资报告邮件。

    Args:
        summary: 投资组合分析汇总数据。
        report_month: 报告月份，如 "2026-02-01"。

    Returns:
        True 发送成功，False 发送失败。
    """
    # 读取 SMTP 配置
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")

    if not all([smtp_host, smtp_user, smtp_password, recipient]):
        print("[错误] SMTP 配置不完整，请检查 .env 文件")
        return False

    # 生成邮件内容
    subject = _build_subject(report_month, summary)
    html_body = build_report_html(summary, report_month)

    # 构建邮件
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # 发送（端口465用SSL直连，其他端口用STARTTLS）
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        print(f"[成功] 报告邮件已发送至 {recipient}")
        return True
    except Exception as e:
        print(f"[错误] 邮件发送失败: {e}")
        return False


def _build_subject(report_month: str, summary: PortfolioSummary) -> str:
    """生成邮件主题。"""
    # 提取年月，如 "2026-02-01" -> "2026年2月"
    parts = report_month.split("-")
    month_str = f"{parts[0]}年{int(parts[1])}月"
    sign = "+" if summary.total_return >= 0 else ""
    return f"投资月报 | {month_str} | 总收益 {sign}{summary.total_return:.2%}"


def build_report_html(summary: PortfolioSummary, report_month: str) -> str:
    """
    生成月度报告的 HTML 内容。

    此函数为纯函数，不依赖外部状态，方便测试和预览。

    Args:
        summary: 投资组合分析汇总。
        report_month: 报告月份。

    Returns:
        完整的 HTML 字符串。
    """
    parts = report_month.split("-")
    month_str = f"{parts[0]}年{int(parts[1])}月"

    # 组合概况
    return_color = "#00c853" if summary.total_return >= 0 else "#ff1744"
    pl_color = "#00c853" if summary.total_profit_loss >= 0 else "#ff1744"

    # 标的明细行
    asset_rows = ""
    for a in summary.asset_analyses:
        cum_color = "#00c853" if a.cumulative_return >= 0 else "#ff1744"
        monthly_str = "-"
        monthly_color = "#333333"
        if a.monthly_return is not None:
            monthly_color = "#00c853" if a.monthly_return >= 0 else "#ff1744"
            monthly_str = f"{a.monthly_return:+.2%}"

        asset_rows += f"""
        <tr>
            <td>{a.name}</td>
            <td>{a.ticker}</td>
            <td>{a.asset_type}</td>
            <td style="text-align:right">{a.base_price:,.4f}</td>
            <td style="text-align:right">{a.current_price:,.4f}</td>
            <td style="text-align:right">${a.total_invested:,.2f}</td>
            <td style="text-align:right">${a.current_value:,.2f}</td>
            <td style="text-align:right;color:{cum_color}">{a.cumulative_return:+.2%}</td>
            <td style="text-align:right;color:{monthly_color}">{monthly_str}</td>
        </tr>"""

    # 各标的涨跌卡片（涨绿底，跌红底）
    asset_cards = '<div style="margin:20px 0">'
    for i, a in enumerate(summary.asset_analyses):
        ret = a.cumulative_return
        bg = "#e8f5e9" if ret >= 0 else "#ffebee"
        color = "#00c853" if ret >= 0 else "#ff1744"
        asset_cards += (
            f'<div style="display:inline-block;background:{bg};padding:12px 20px;'
            f'border-radius:8px;margin:0 12px 12px 0;text-align:center;min-width:140px">'
            f'<div style="color:#666;font-size:13px">{a.asset_type}</div>'
            f'<div style="font-size:18px;font-weight:600">{a.name}</div>'
            f'<div style="color:{color};font-size:16px">{ret:+.2%}</div>'
            f'</div>'
        )
    asset_cards += '</div>'

    # 最佳/最差
    best_section = ""
    if summary.best_performer and summary.best_performer.monthly_return is not None:
        b = summary.best_performer
        best_section = (
            f'<div style="display:inline-block;background:#e8f5e9;padding:12px 20px;'
            f'border-radius:8px;margin:0 12px 12px 0;text-align:center;min-width:140px">'
            f'<div style="color:#666;font-size:13px">本月最佳</div>'
            f'<div style="font-size:18px;font-weight:600">{b.name}</div>'
            f'<div style="color:#00c853;font-size:16px">{b.monthly_return:+.2%}</div>'
            f'</div>'
        )

    worst_section = ""
    if summary.worst_performer and summary.worst_performer.monthly_return is not None:
        w = summary.worst_performer
        worst_section = (
            f'<div style="display:inline-block;background:#ffebee;padding:12px 20px;'
            f'border-radius:8px;margin:0 12px 12px 0;text-align:center;min-width:140px">'
            f'<div style="color:#666;font-size:13px">本月最差</div>'
            f'<div style="font-size:18px;font-weight:600">{w.name}</div>'
            f'<div style="color:#ff1744;font-size:16px">{w.monthly_return:+.2%}</div>'
            f'</div>'
        )

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
             max-width:800px;margin:0 auto;padding:20px;color:#333">

    <h1 style="color:#1a1a2e;border-bottom:3px solid #e2e8f0;padding-bottom:12px">
        {month_str} 投资月报
    </h1>

    <!-- 组合概况 -->
    <table style="width:100%;border-collapse:collapse;margin:20px 0">
        <tr>
            <td style="text-align:center;padding:16px;background:#f8f9fa;border-radius:8px">
                <div style="color:#666;font-size:13px">总投入</div>
                <div style="font-size:22px;font-weight:700">${summary.total_invested:,.2f}</div>
            </td>
            <td style="width:12px"></td>
            <td style="text-align:center;padding:16px;background:#f8f9fa;border-radius:8px">
                <div style="color:#666;font-size:13px">总当前价值</div>
                <div style="font-size:22px;font-weight:700">${summary.total_current_value:,.2f}</div>
            </td>
            <td style="width:12px"></td>
            <td style="text-align:center;padding:16px;background:#f8f9fa;border-radius:8px">
                <div style="color:#666;font-size:13px">总收益率</div>
                <div style="font-size:22px;font-weight:700;color:{return_color}">
                    {summary.total_return:+.2%}
                </div>
            </td>
            <td style="width:12px"></td>
            <td style="text-align:center;padding:16px;background:#f8f9fa;border-radius:8px">
                <div style="color:#666;font-size:13px">盈亏</div>
                <div style="font-size:22px;font-weight:700;color:{pl_color}">
                    ${summary.total_profit_loss:+,.2f}
                </div>
            </td>
        </tr>
    </table>

    <!-- 最佳/最差 -->
    {best_section}{worst_section}

    <!-- 各标的涨跌卡片 -->
    {asset_cards}

    <!-- 标的明细 -->
    <h2 style="color:#16213e;margin-top:28px;border-bottom:2px solid #e2e8f0;padding-bottom:8px">
        标的明细
    </h2>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
        <thead>
            <tr style="background:#f1f3f5;text-align:left">
                <th style="padding:10px 8px">标的</th>
                <th style="padding:10px 8px">代码</th>
                <th style="padding:10px 8px">类别</th>
                <th style="padding:10px 8px;text-align:right">基准价</th>
                <th style="padding:10px 8px;text-align:right">当前价</th>
                <th style="padding:10px 8px;text-align:right">投入</th>
                <th style="padding:10px 8px;text-align:right">当前价值</th>
                <th style="padding:10px 8px;text-align:right">累计</th>
                <th style="padding:10px 8px;text-align:right">本月</th>
            </tr>
        </thead>
        <tbody>
            {asset_rows}
        </tbody>
    </table>

    <p style="color:#999;font-size:12px;margin-top:32px;border-top:1px solid #e2e8f0;padding-top:12px">
        此报告由 Invest Agent 自动生成 | 数据来源: Yahoo Finance / AKShare
    </p>

</body>
</html>"""

    return html
