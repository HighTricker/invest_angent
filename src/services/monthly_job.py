"""
月度定时任务模块。

每月2日自动执行完整流程：采集价格 → 分析数据 → 发送邮件。
也可手动调用进行补录或测试。
"""

import sys
from datetime import datetime, date

from src.models.database import init_db
from src.services.collector import collect_all
from src.services.analyzer import analyze_portfolio
from src.services.email_sender import send_monthly_report


def run_monthly_job(
    target_date: str | None = None,
    db_path: str | None = None,
) -> bool:
    """
    执行完整的月度任务流程。

    流程：
    1. 确保数据库已初始化
    2. 采集所有标的在目标月份的价格
    3. 分析投资组合表现
    4. 发送邮件报告

    Args:
        target_date: 目标月份日期，格式 "YYYY-MM-DD"。
                     为 None 时自动取当月1日（如今天是2月2日，则取 "2026-02-01"）。
        db_path: 数据库路径，为 None 时使用默认路径。

    Returns:
        True 全部成功，False 有步骤失败。
    """
    # 确定目标日期
    if target_date is None:
        today = date.today()
        target_date = f"{today.year}-{today.month:02d}-01"

    print(f"====== 月度任务开始 | 目标月份: {target_date} ======")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 步骤1: 确保数据库已初始化
    print("\n[步骤1] 初始化数据库...")
    init_db(db_path)
    print("  数据库就绪")

    # 步骤2: 采集价格
    print(f"\n[步骤2] 采集 {target_date} 的价格数据...")
    results = collect_all(target_date, db_path)
    success_count = sum(1 for v in results.values() if v is not None)
    if success_count == 0 and len(results) > 0:
        print("[错误] 所有标的价格采集失败，终止任务")
        return False

    # 步骤3: 分析数据
    print(f"\n[步骤3] 分析投资组合表现...")
    summary = analyze_portfolio(target_date, db_path)
    if not summary.asset_analyses:
        print("[错误] 无分析数据，终止任务")
        return False

    print(f"  总投入: ${summary.total_invested:,.2f}")
    print(f"  总价值: ${summary.total_current_value:,.2f}")
    print(f"  总收益率: {summary.total_return:+.2%}")

    # 步骤4: 发送邮件
    print(f"\n[步骤4] 发送月度报告邮件...")
    email_sent = send_monthly_report(summary, target_date)
    if not email_sent:
        print("[警告] 邮件发送失败，但数据已成功采集和分析")

    print(f"\n====== 月度任务完成 ======")
    return True


# 支持命令行直接运行：python -m src.services.monthly_job [日期]
if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run_monthly_job(target)
