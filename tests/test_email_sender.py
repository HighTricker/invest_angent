"""
邮件报告模块测试。

验证 HTML 报告生成逻辑，不实际发送邮件。
"""

import sys
from src.services.analyzer import AssetAnalysis, PortfolioSummary
from src.services.email_sender import build_report_html, _build_subject


def _mock_summary() -> PortfolioSummary:
    """构造模拟的投资组合分析数据。"""
    google = AssetAnalysis(
        asset_id=1, name="Google", ticker="GOOGL", asset_type="美股",
        base_price=313.0, current_price=338.0, previous_price=320.0,
        total_invested=50.0,
        cumulative_return=0.0799, monthly_return=0.0563,
        current_value=53.99, profit_loss=3.99,
    )
    apple = AssetAnalysis(
        asset_id=2, name="Apple", ticker="AAPL", asset_type="美股",
        base_price=283.1, current_price=270.0, previous_price=280.0,
        total_invested=100.0,
        cumulative_return=-0.0463, monthly_return=-0.0357,
        current_value=95.37, profit_loss=-4.63,
    )
    return PortfolioSummary(
        total_invested=150.0,
        total_current_value=149.36,
        total_profit_loss=-0.64,
        total_return=-0.0043,
        best_performer=google,
        worst_performer=apple,
        asset_analyses=[google, apple],
    )


def test_build_subject():
    """测试邮件主题生成。"""
    summary = _mock_summary()
    subject = _build_subject("2026-02-01", summary)
    assert "2026" in subject, "主题应包含年份"
    assert "2" in subject, "主题应包含月份"
    assert "%" in subject, "主题应包含收益率"
    print(f"[PASS] 邮件主题: {subject}")


def test_build_report_html():
    """测试 HTML 报告生成。"""
    summary = _mock_summary()
    html = build_report_html(summary, "2026-02-01")

    # 验证关键内容存在
    assert "2026" in html, "报告应包含年份"
    assert "Google" in html, "报告应包含标的名称"
    assert "GOOGL" in html, "报告应包含交易代码"
    assert "$150.00" in html, "报告应包含总投入"
    assert "本月最佳" in html, "报告应包含最佳标的"
    assert "本月最差" in html, "报告应包含最差标的"
    assert "#00c853" in html, "报告应包含涨的绿色"
    assert "#ff1744" in html, "报告应包含跌的红色"

    print("[PASS] HTML 报告生成成功")
    print(f"  HTML 长度: {len(html)} 字符")

    # 将报告写入临时文件供人工预览
    preview_path = "data/report_preview.html"
    import os
    os.makedirs("data", exist_ok=True)
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  预览文件: {preview_path} (可用浏览器打开查看效果)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    test_build_subject()
    test_build_report_html()
    print("\n全部测试完成!")
