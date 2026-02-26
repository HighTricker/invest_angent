"""
数据分析模块测试。

使用临时数据库和模拟数据，验证涨跌幅、仓位价值等计算逻辑。
"""

import sys
import os
import tempfile
from src.models.database import init_db, get_connection
from src.services.analyzer import analyze_asset, analyze_portfolio


def _setup_test_db() -> str:
    """创建临时测试数据库并插入模拟数据，返回数据库路径。"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path)

    conn = get_connection(db_path)

    # 插入两个标的
    conn.execute(
        "INSERT INTO assets (id, name, ticker, asset_type, base_price, base_date) "
        "VALUES (1, 'Google', 'GOOGL', '美股', 100.0, '2025-12-01')"
    )
    conn.execute(
        "INSERT INTO assets (id, name, ticker, asset_type, base_price, base_date) "
        "VALUES (2, 'Apple', 'AAPL', '美股', 200.0, '2025-12-01')"
    )

    # 插入持仓：Google 投入 50 美元，Apple 投入 100 美元
    conn.execute(
        "INSERT INTO positions (asset_id, total_invested) VALUES (1, 50.0)"
    )
    conn.execute(
        "INSERT INTO positions (asset_id, total_invested) VALUES (2, 100.0)"
    )

    # 插入月度价格数据
    # Google: 基准100 → 1月110（+10%）→ 2月105（累计+5%，月度-4.55%）
    conn.execute(
        "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
        "VALUES (1, '2026-01-01', 110.0)"
    )
    conn.execute(
        "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
        "VALUES (1, '2026-02-01', 105.0)"
    )

    # Apple: 基准200 → 1月190（-5%）→ 2月210（累计+5%，月度+10.53%）
    conn.execute(
        "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
        "VALUES (2, '2026-01-01', 190.0)"
    )
    conn.execute(
        "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
        "VALUES (2, '2026-02-01', 210.0)"
    )

    conn.commit()
    conn.close()
    return db_path


def _approx_equal(a: float, b: float, tol: float = 0.0001) -> bool:
    """浮点数近似比较。"""
    return abs(a - b) < tol


def test_single_asset_analysis():
    """测试单标的分析：Google 在 2026-02-01 的各项指标。"""
    db_path = _setup_test_db()
    try:
        result = analyze_asset(1, "2026-02-01", db_path)
        assert result is not None, "分析结果不应为 None"

        # 累计涨跌幅 = (105 - 100) / 100 = 0.05 (+5%)
        assert _approx_equal(result.cumulative_return, 0.05), \
            f"累计涨跌幅错误: 期望=0.05, 实际={result.cumulative_return}"

        # 月度涨跌幅 = (105 - 110) / 110 = -0.04545 (-4.55%)
        assert result.monthly_return is not None
        assert _approx_equal(result.monthly_return, -0.04545, tol=0.001), \
            f"月度涨跌幅错误: 期望=-0.04545, 实际={result.monthly_return}"

        # 当前仓位 = 50 × (1 + 0.05) = 52.5
        assert _approx_equal(result.current_value, 52.5), \
            f"当前仓位错误: 期望=52.5, 实际={result.current_value}"

        # 盈亏 = 52.5 - 50 = 2.5
        assert _approx_equal(result.profit_loss, 2.5), \
            f"盈亏错误: 期望=2.5, 实际={result.profit_loss}"

        print("[PASS] Google 单标的分析正确")
    finally:
        os.unlink(db_path)


def test_first_month_no_monthly_return():
    """测试首月（无上月数据）时月度涨跌幅应为 None。"""
    db_path = _setup_test_db()
    try:
        result = analyze_asset(1, "2026-01-01", db_path)
        assert result is not None
        assert result.monthly_return is None, \
            f"首月月度涨跌幅应为 None, 实际={result.monthly_return}"
        print("[PASS] 首月月度涨跌幅正确为 None")
    finally:
        os.unlink(db_path)


def test_portfolio_analysis():
    """测试投资组合汇总分析。"""
    db_path = _setup_test_db()
    try:
        summary = analyze_portfolio("2026-02-01", db_path)

        # 总投入 = 50 + 100 = 150
        assert _approx_equal(summary.total_invested, 150.0), \
            f"总投入错误: 期望=150, 实际={summary.total_invested}"

        # Google 当前价值 = 50 × 1.05 = 52.5
        # Apple 当前价值 = 100 × 1.05 = 105
        # 总当前价值 = 52.5 + 105 = 157.5
        assert _approx_equal(summary.total_current_value, 157.5), \
            f"总价值错误: 期望=157.5, 实际={summary.total_current_value}"

        # 总收益率 = (157.5 - 150) / 150 = 0.05 (+5%)
        assert _approx_equal(summary.total_return, 0.05), \
            f"总收益率错误: 期望=0.05, 实际={summary.total_return}"

        # 本月最佳: Apple（月度+10.53%）
        assert summary.best_performer is not None
        assert summary.best_performer.ticker == "AAPL", \
            f"最佳标的错误: 期望=AAPL, 实际={summary.best_performer.ticker}"

        # 本月最差: Google（月度-4.55%）
        assert summary.worst_performer is not None
        assert summary.worst_performer.ticker == "GOOGL", \
            f"最差标的错误: 期望=GOOGL, 实际={summary.worst_performer.ticker}"

        print("[PASS] 投资组合汇总分析正确")
        print(f"  总投入: ${summary.total_invested:.2f}")
        print(f"  总价值: ${summary.total_current_value:.2f}")
        print(f"  总收益率: {summary.total_return:.2%}")
        print(f"  最佳: {summary.best_performer.name} ({summary.best_performer.monthly_return:.2%})")
        print(f"  最差: {summary.worst_performer.name} ({summary.worst_performer.monthly_return:.2%})")
    finally:
        os.unlink(db_path)


def test_zero_investment():
    """测试零投入时不会除零报错。"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path)

    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO assets (id, name, ticker, asset_type, base_price, base_date) "
        "VALUES (1, 'Test', 'TEST', '测试', 100.0, '2025-12-01')"
    )
    # 不插入 positions 记录（投入为 0）
    conn.execute(
        "INSERT INTO monthly_prices (asset_id, record_date, close_price) "
        "VALUES (1, '2026-01-01', 120.0)"
    )
    conn.commit()
    conn.close()

    try:
        result = analyze_asset(1, "2026-01-01", db_path)
        assert result is not None
        assert _approx_equal(result.current_value, 0.0), "零投入时仓位价值应为 0"
        print("[PASS] 零投入场景处理正确")
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    test_single_asset_analysis()
    test_first_month_no_monthly_return()
    test_portfolio_analysis()
    test_zero_investment()
    print("\n全部测试完成!")
