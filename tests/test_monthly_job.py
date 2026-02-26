"""
月度定时任务测试。

使用临时数据库，验证完整流程（采集→分析→报告生成）的串联。
不实际发送邮件（因为没有配置 SMTP）。
"""

import sys
import os
import tempfile

from src.models.database import init_db, get_connection
from src.services.monthly_job import run_monthly_job


def _setup_test_db() -> str:
    """创建临时数据库并插入测试标的。"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(db_path)

    conn = get_connection(db_path)
    # 插入一个真实标的用于测试（GOOGL 数据源可用）
    conn.execute(
        "INSERT INTO assets (name, ticker, asset_type, base_price, base_date) "
        "VALUES ('Google', 'GOOGL', '美股', 313.0, '2025-12-01')"
    )
    # 插入持仓
    conn.execute(
        "INSERT INTO positions (asset_id, total_invested) VALUES (1, 50.0)"
    )
    conn.commit()
    conn.close()
    return db_path


def test_monthly_job_flow():
    """测试完整月度任务流程（采集+分析），邮件发送会因无 SMTP 配置而跳过。"""
    db_path = _setup_test_db()
    try:
        # 执行月度任务（2026-01-01 的数据）
        # 邮件会失败（无 SMTP 配置），但采集和分析应该成功
        run_monthly_job("2026-01-01", db_path)

        # 验证价格已写入数据库
        conn = get_connection(db_path)
        record = conn.execute(
            "SELECT close_price FROM monthly_prices "
            "WHERE asset_id = 1 AND record_date = '2026-01-01'"
        ).fetchone()
        conn.close()

        assert record is not None, "价格数据应已写入数据库"
        assert record["close_price"] > 0, "价格应大于 0"
        print(f"[PASS] 流程串联成功: GOOGL 2026-01-01 价格 = {record['close_price']:.2f}")
    finally:
        os.unlink(db_path)


def test_idempotent():
    """测试重复执行不会产生重复数据。"""
    db_path = _setup_test_db()
    try:
        run_monthly_job("2026-01-01", db_path)
        run_monthly_job("2026-01-01", db_path)  # 第二次应跳过已有数据

        conn = get_connection(db_path)
        count = conn.execute(
            "SELECT COUNT(*) as cnt FROM monthly_prices "
            "WHERE asset_id = 1 AND record_date = '2026-01-01'"
        ).fetchone()["cnt"]
        conn.close()

        assert count == 1, f"应只有1条记录，实际有 {count} 条"
        print("[PASS] 重复执行不产生重复数据")
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 测试完整流程串联 ===")
    test_monthly_job_flow()
    print("\n=== 测试幂等性 ===")
    test_idempotent()
    print("\n全部测试完成!")
